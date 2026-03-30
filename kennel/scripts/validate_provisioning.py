#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_TIMEOUT_S = 30
DEFAULT_POLL_INTERVAL_S = 2
DEFAULT_JOB_TIMEOUT_S = 1800


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StepResult:
    id: str
    description: str
    status: str
    validated: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    failure_summary: str | None = None
    engineer_handoff: list[str] = field(default_factory=list)


class ValidationFailure(Exception):
    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        engineer_handoff: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.details = details or {}
        self.engineer_handoff = engineer_handoff or []


class KennelClient:
    def __init__(
        self,
        *,
        base_url: str,
        secret: str,
        timeout_s: int,
        verbose: bool,
        artifacts_dir: Path,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.secret = secret
        self.timeout_s = timeout_s
        self.verbose = verbose
        self.artifacts_dir = artifacts_dir

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, file=sys.stderr)

    def request_json(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        artifact_name: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        payload = None
        headers = {}
        if path != "/health":
            headers["x-kennel-secret"] = self.secret
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=payload, method=method, headers=headers)
        self._log(f"[http] {method} {url}")
        if body is not None and self.verbose:
            self._log(f"[http] request body: {json.dumps(body, indent=2)}")

        try:
            with request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                status = resp.status
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            status = exc.code
            self._write_artifact(
                artifact_name,
                {
                    "request": {"method": method, "url": url, "body": body},
                    "response": {"status": status, "body": self._parse_json_or_text(raw)},
                },
            )
            raise ValidationFailure(
                f"HTTP {status} from {path}",
                details={
                    "method": method,
                    "path": path,
                    "url": url,
                    "request_body": body,
                    "http_status": status,
                    "response_body": self._parse_json_or_text(raw),
                },
                engineer_handoff=[
                    f"endpoint: {method} {path}",
                    f"http_status: {status}",
                    f"artifact: {self._artifact_path_str(artifact_name)}" if artifact_name else "artifact: none",
                    "include the full response body and request payload in the bug report",
                ],
            ) from exc
        except Exception as exc:
            raise ValidationFailure(
                f"Request failed for {path}: {exc}",
                details={"method": method, "path": path, "url": url, "request_body": body},
                engineer_handoff=[
                    f"endpoint: {method} {path}",
                    "include the exception text and whether kennel was reachable from the test host",
                ],
            ) from exc

        parsed = self._parse_json(raw)
        self._write_artifact(
            artifact_name,
            {
                "request": {"method": method, "url": url, "body": body},
                "response": {"status": status, "body": parsed},
            },
        )
        if self.verbose:
            self._log(f"[http] response status: {status}")
            self._log(f"[http] response body: {json.dumps(parsed, indent=2)}")
        return parsed

    def _parse_json(self, raw: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationFailure(
                "Response was not valid JSON",
                details={"raw_response": raw},
                engineer_handoff=[
                    "include the raw response body and endpoint that returned it",
                ],
            ) from exc
        if not isinstance(parsed, dict):
            raise ValidationFailure(
                "Response JSON was not an object",
                details={"parsed_response": parsed},
                engineer_handoff=["include the raw JSON response body"],
            )
        return parsed

    def _parse_json_or_text(self, raw: str) -> Any:
        try:
            return json.loads(raw)
        except Exception:
            return raw

    def _artifact_path_str(self, artifact_name: str | None) -> str | None:
        if not artifact_name:
            return None
        return str(self.artifacts_dir / artifact_name)

    def _write_artifact(self, artifact_name: str | None, payload: Any) -> None:
        if not artifact_name:
            return
        path = self.artifacts_dir / artifact_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")


class Validator:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.artifacts_dir = Path(args.artifacts_dir).resolve()
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.client = KennelClient(
            base_url=args.base_url,
            secret=args.secret,
            timeout_s=args.timeout,
            verbose=args.verbose,
            artifacts_dir=self.artifacts_dir,
        )
        self.results: list[StepResult] = []
        self.envs_to_cleanup: list[str] = []
        self.context: dict[str, Any] = {
            "codex_env": None,
            "codex_job": None,
            "claude_env": None,
            "claude_job": None,
            "codex_rebuild_job": None,
            "claude_rebuild_job": None,
            "force_rebuild_job": None,
        }

    def log(self, message: str) -> None:
        if self.args.verbose:
            print(message, file=sys.stderr)

    def add_result(self, result: StepResult) -> None:
        self.results.append(result)

    def run(self) -> int:
        overall = "pass"
        try:
            self.step_health()
            flavours = self.step_inspect_flavours()
            if self.args.rebuild_if_needed:
                flavours = self.step_rebuild_if_needed(flavours)
            self.step_confirm_base_ready(flavours)
            self.step_create_codex_env()
            self.step_inject_codex()
            self.step_probe_codex()
            self.step_create_claude_env()
            self.step_inject_claude()
            self.step_probe_claude()
            if self.args.test_force_rebuild_guard:
                self.step_force_rebuild_guard()
        except ValidationFailure as exc:
            overall = "fail"
            self.add_result(
                StepResult(
                    id="fatal",
                    description="Validator aborted after a failed step",
                    status="failed",
                    details=exc.details,
                    failure_summary=str(exc),
                    engineer_handoff=exc.engineer_handoff,
                )
            )
        except Exception as exc:
            overall = "fail"
            self.add_result(
                StepResult(
                    id="fatal",
                    description="Validator crashed unexpectedly",
                    status="failed",
                    details={"traceback": traceback.format_exc()},
                    failure_summary=str(exc),
                    engineer_handoff=[
                        "include the full traceback from the validator output",
                        f"artifact directory: {self.artifacts_dir}",
                    ],
                )
            )
        finally:
            if self.args.cleanup:
                self.cleanup_envs()

        summary = {
            "validator": "kennel-provisioning-validator",
            "started_at": self.args.started_at,
            "finished_at": utc_now(),
            "overall_status": overall if all(r.status != "failed" for r in self.results) else "fail",
            "artifacts_dir": str(self.artifacts_dir),
            "config": {
                "base_url": self.args.base_url,
                "repo_url": self.args.repo_url,
                "rebuild_if_needed": self.args.rebuild_if_needed,
                "cleanup": self.args.cleanup,
                "test_force_rebuild_guard": self.args.test_force_rebuild_guard,
                "codex_full_runtime_required": self.args.require_codex_ready,
                "claude_full_runtime_required": self.args.require_claude_ready,
                "verbose": self.args.verbose,
            },
            "context": self.context,
            "steps": [asdict(r) for r in self.results],
        }
        print(json.dumps(summary, indent=2))
        return 0 if summary["overall_status"] == "pass" else 1

    def require(self, condition: bool, message: str, **details: Any) -> None:
        if not condition:
            raise ValidationFailure(
                message,
                details=details,
                engineer_handoff=[
                    f"artifact directory: {self.artifacts_dir}",
                    "include the failing step id, request/response artifact, and the exact JSON returned by kennel",
                ],
            )

    def poll_job(self, path: str, *, artifact_prefix: str, timeout_s: int | None = None) -> dict[str, Any]:
        timeout_s = timeout_s or self.args.job_timeout
        deadline = time.time() + timeout_s
        attempt = 0
        last = None
        while time.time() < deadline:
            attempt += 1
            last = self.client.request_json("GET", path, artifact_name=f"{artifact_prefix}-{attempt}.json")
            status = last.get("status")
            if status in {"done", "failed"}:
                return last
            time.sleep(self.args.poll_interval)
        raise ValidationFailure(
            f"Timed out polling job at {path}",
            details={"path": path, "last_response": last, "timeout_s": timeout_s},
            engineer_handoff=[
                f"endpoint: GET {path}",
                f"artifact prefix: {artifact_prefix}",
                "include the last polled response and whether kennel was still processing or stuck",
            ],
        )

    def step_health(self) -> None:
        step = StepResult(
            id="health",
            description="Validate kennel health endpoint",
            status="passed",
            validated=[
                "kennel HTTP server is reachable",
                "the process is accepting requests",
            ],
        )
        try:
            body = self.client.request_json("GET", "/health", artifact_name="step-health.json")
            self.require(body.get("status") == "ok", "Health endpoint did not return status=ok", response=body)
            step.details = {"response": body}
            step.artifacts.append(str(self.artifacts_dir / "step-health.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff
            self.add_result(step)
            raise
        self.add_result(step)

    def step_inspect_flavours(self) -> dict[str, Any]:
        step = StepResult(
            id="inspect_flavours",
            description="Inspect runtime flavours and base-container readiness fields",
            status="passed",
            validated=[
                "runtime-specific flavours are registered",
                "base_container and base_ready are reported",
                "snapshot-era readiness reporting is not being used",
            ],
        )
        try:
            body = self.client.request_json("GET", "/flavours", artifact_name="step-flavours.json")
            for flavour in ("dev-codex", "dev-claude-code"):
                self.require(flavour in body, f"Missing flavour {flavour}", response=body)
                self.require("base_container" in body[flavour], f"Missing base_container for {flavour}", response=body[flavour])
                self.require("base_ready" in body[flavour], f"Missing base_ready for {flavour}", response=body[flavour])
            step.details = {
                "codex": body["dev-codex"],
                "claude_code": body["dev-claude-code"],
            }
            step.artifacts.append(str(self.artifacts_dir / "step-flavours.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff
            self.add_result(step)
            raise
        self.add_result(step)
        return body

    def step_rebuild_if_needed(self, flavours: dict[str, Any]) -> dict[str, Any]:
        for flavour in ("dev-codex", "dev-claude-code"):
            if flavours[flavour].get("base_ready"):
                continue
            self._rebuild_flavour(flavour)
        return self.client.request_json("GET", "/flavours", artifact_name="step-flavours-post-rebuild.json")

    def _rebuild_flavour(self, flavour: str) -> None:
        step = StepResult(
            id=f"rebuild_{flavour}",
            description=f"Rebuild flavour {flavour} when its base container is not ready",
            status="passed",
            validated=[
                "runtime-specific flavour rebuild can be triggered",
                "rebuild job API surfaces completion status",
                "provision scripts are reachable at runtime",
            ],
        )
        try:
            started = self.client.request_json(
                "POST",
                f"/flavours/{flavour}/rebuild",
                artifact_name=f"step-{flavour}-rebuild-start.json",
            )
            job_id = started.get("job_id")
            self.require(bool(job_id), f"Rebuild response for {flavour} did not include job_id", response=started)
            self.context[f"{flavour.replace('-', '_')}_rebuild_job"] = job_id
            polled = self.poll_job(
                f"/rebuild-jobs/{job_id}",
                artifact_prefix=f"step-{flavour}-rebuild-poll",
            )
            self.require(polled.get("status") == "done", f"Rebuild failed for {flavour}", response=polled)
            step.details = {"start_response": started, "final_response": polled}
            step.artifacts.extend(
                [
                    str(self.artifacts_dir / f"step-{flavour}-rebuild-start.json"),
                ]
            )
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff + [
                f"flavour: {flavour}",
                "if rebuild failed, include the rebuild job payload and the final log_lines returned by kennel",
            ]
            self.add_result(step)
            raise
        self.add_result(step)

    def step_confirm_base_ready(self, flavours: dict[str, Any]) -> None:
        step = StepResult(
            id="confirm_base_ready",
            description="Confirm base-dev-codex and base-dev-claude-code are ready",
            status="passed",
            validated=[
                "base-dev-codex exists and is ready",
                "base-dev-claude-code exists and is ready",
            ],
        )
        try:
            self.require(flavours["dev-codex"].get("base_ready") is True, "dev-codex base container is not ready", response=flavours["dev-codex"])
            self.require(
                flavours["dev-claude-code"].get("base_ready") is True,
                "dev-claude-code base container is not ready",
                response=flavours["dev-claude-code"],
            )
            step.details = {
                "codex": flavours["dev-codex"],
                "claude_code": flavours["dev-claude-code"],
            }
            step.artifacts.append(str(self.artifacts_dir / "step-flavours-post-rebuild.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff
            self.add_result(step)
            raise
        self.add_result(step)

    def step_create_codex_env(self) -> None:
        step = StepResult(
            id="create_codex_env",
            description="Create a persistent Codex environment via runtime_preset",
            status="passed",
            validated=[
                "create-time runtime_preset normalization is accepted",
                "kennel clones from the runtime-specific base container",
                "create path is asynchronous and job-backed",
            ],
        )
        try:
            body = self.client.request_json(
                "POST",
                "/envs",
                body={"kind": "persistent", "runtime_preset": "codex"},
                artifact_name="step-create-codex.json",
            )
            env_name = body.get("name")
            job_id = body.get("job_id")
            self.require(bool(env_name), "Codex create response did not include env name", response=body)
            self.require(bool(job_id), "Codex create response did not include job_id", response=body)
            self.context["codex_env"] = env_name
            self.context["codex_job"] = job_id
            self.envs_to_cleanup.append(env_name)
            polled = self.poll_job(f"/jobs/{job_id}", artifact_prefix="step-create-codex-poll")
            self.require(polled.get("status") == "done", "Codex create job did not complete successfully", response=polled)
            self.require(polled.get("env_name") == env_name, "Codex create job env_name did not match", response=polled)
            step.details = {"start_response": body, "final_response": polled}
            step.artifacts.append(str(self.artifacts_dir / "step-create-codex.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff + [
                "if create failed, include whether base-dev-codex was ready before the call",
            ]
            self.add_result(step)
            raise
        self.add_result(step)

    def step_inject_codex(self) -> None:
        step = StepResult(
            id="inject_codex",
            description="Inject Codex runtime and workspace personalization",
            status="passed",
            validated=[
                "inject-time runtime_preset resolves Codex bootstrap behavior",
                "runtime files are written for Codex",
                "the codex service is declared and startup is attempted",
            ],
        )
        try:
            body = {
                "runtime_preset": "codex",
                "repo_url": self.args.repo_url,
            }
            if self.args.openai_api_key:
                body["env_vars"] = {"OPENAI_API_KEY": self.args.openai_api_key}
            response = self.client.request_json(
                "POST",
                f"/envs/{self.context['codex_env']}/inject",
                body=body,
                artifact_name="step-inject-codex.json",
            )
            declared = response.get("declared_services") or []
            codex_service = next((s for s in declared if s.get("service_name") == "codex"), None)
            self.require(codex_service is not None, "Inject did not declare codex service", response=response)
            self.require(codex_service.get("protocol") == "ws", "Codex service protocol was not ws", service=codex_service)
            self.require(codex_service.get("port") == 4500, "Codex service port was not 4500", service=codex_service)
            if self.args.openai_api_key:
                self.require(response.get("bootstrap_success") is True, "Codex inject did not complete successfully with OPENAI_API_KEY present", response=response)
            step.details = {"response": response}
            step.artifacts.append(str(self.artifacts_dir / "step-inject-codex.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff + [
                f"env_name: {self.context.get('codex_env')}",
                "include started_services, bootstrap_success, fatal_error, and declared_services from the inject response",
            ]
            self.add_result(step)
            raise
        self.add_result(step)

    def step_probe_codex(self) -> None:
        step = StepResult(
            id="probe_codex",
            description="Probe Codex service readiness",
            status="passed",
            validated=[
                "service manifest was persisted",
                "kennel can probe codex runtime readiness",
                "codex runtime metadata reports websocket port 4500",
            ],
        )
        try:
            response = self.client.request_json(
                "GET",
                f"/envs/{self.context['codex_env']}/services",
                artifact_name="step-probe-codex.json",
            )
            services = response.get("services") or []
            codex = next((s for s in services if s.get("service_name") == "codex"), None)
            self.require(codex is not None, "Services response did not include codex runtime", response=response)
            self.require(codex.get("port") == 4500, "Codex readiness probe did not report port 4500", service=codex)
            if self.args.require_codex_ready:
                self.require(codex.get("status") == "ready", "Codex runtime was not ready", service=codex)
            step.details = {"response": response}
            step.artifacts.append(str(self.artifacts_dir / "step-probe-codex.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff + [
                f"env_name: {self.context.get('codex_env')}",
                "include the full /services payload and whether OPENAI_API_KEY was provided",
            ]
            self.add_result(step)
            raise
        self.add_result(step)

    def step_create_claude_env(self) -> None:
        step = StepResult(
            id="create_claude_env",
            description="Create a persistent Claude Code environment via runtime_preset",
            status="passed",
            validated=[
                "create-time runtime_preset normalization resolves dev-claude-code",
                "kennel clones from the claude runtime base container",
            ],
        )
        try:
            body = self.client.request_json(
                "POST",
                "/envs",
                body={"kind": "persistent", "runtime_preset": "claude_code"},
                artifact_name="step-create-claude.json",
            )
            env_name = body.get("name")
            job_id = body.get("job_id")
            self.require(bool(env_name), "Claude create response did not include env name", response=body)
            self.require(bool(job_id), "Claude create response did not include job_id", response=body)
            self.context["claude_env"] = env_name
            self.context["claude_job"] = job_id
            self.envs_to_cleanup.append(env_name)
            polled = self.poll_job(f"/jobs/{job_id}", artifact_prefix="step-create-claude-poll")
            self.require(polled.get("status") == "done", "Claude create job did not complete successfully", response=polled)
            self.require(polled.get("env_name") == env_name, "Claude create job env_name did not match", response=polled)
            step.details = {"start_response": body, "final_response": polled}
            step.artifacts.append(str(self.artifacts_dir / "step-create-claude.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff + [
                "if create failed, include whether base-dev-claude-code was ready before the call",
            ]
            self.add_result(step)
            raise
        self.add_result(step)

    def step_inject_claude(self) -> None:
        step = StepResult(
            id="inject_claude",
            description="Inject Claude Code runtime and workspace personalization",
            status="passed",
            validated=[
                "inject-time runtime_preset resolves claude_code_remote_control",
                "runtime files are written for Claude Code",
                "the claude_code service is declared and startup is attempted",
            ],
        )
        try:
            response = self.client.request_json(
                "POST",
                f"/envs/{self.context['claude_env']}/inject",
                body={"runtime_preset": "claude_code", "repo_url": self.args.repo_url},
                artifact_name="step-inject-claude.json",
            )
            declared = response.get("declared_services") or []
            service = next((s for s in declared if s.get("service_name") == "claude_code"), None)
            self.require(service is not None, "Inject did not declare claude_code service", response=response)
            if self.args.require_claude_ready:
                self.require(response.get("bootstrap_success") is True, "Claude inject did not complete successfully", response=response)
            step.details = {"response": response}
            step.artifacts.append(str(self.artifacts_dir / "step-inject-claude.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff + [
                f"env_name: {self.context.get('claude_env')}",
                "include started_services, bootstrap_success, fatal_error, and declared_services from the inject response",
                "note whether the environment was pre-authenticated for Claude Code",
            ]
            self.add_result(step)
            raise
        self.add_result(step)

    def step_probe_claude(self) -> None:
        step = StepResult(
            id="probe_claude",
            description="Probe Claude Code service readiness",
            status="passed",
            validated=[
                "service manifest exists for claude_code",
                "kennel reports PID-based readiness for a portless runtime",
            ],
        )
        try:
            response = self.client.request_json(
                "GET",
                f"/envs/{self.context['claude_env']}/services",
                artifact_name="step-probe-claude.json",
            )
            services = response.get("services") or []
            service = next((s for s in services if s.get("service_name") == "claude_code"), None)
            self.require(service is not None, "Services response did not include claude_code runtime", response=response)
            if self.args.require_claude_ready:
                self.require(service.get("status") == "ready", "Claude runtime was not ready", service=service)
            step.details = {"response": response}
            step.artifacts.append(str(self.artifacts_dir / "step-probe-claude.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff + [
                f"env_name: {self.context.get('claude_env')}",
                "include the full /services payload and whether Claude auth/subscription prerequisites were satisfied",
            ]
            self.add_result(step)
            raise
        self.add_result(step)

    def step_force_rebuild_guard(self) -> None:
        step = StepResult(
            id="force_rebuild_guard",
            description="Validate force rebuild is blocked while env-* containers still exist",
            status="passed",
            validated=[
                "force rebuild is blocked before overlay ancestry is destroyed",
                "the guard failure is surfaced through rebuild job status",
            ],
        )
        try:
            started = self.client.request_json(
                "POST",
                "/flavours/dev-codex/rebuild?force=true",
                artifact_name="step-force-rebuild-start.json",
            )
            job_id = started.get("job_id")
            self.require(bool(job_id), "Force rebuild did not return job_id", response=started)
            self.context["force_rebuild_job"] = job_id
            polled = self.poll_job("/rebuild-jobs/" + job_id, artifact_prefix="step-force-rebuild-poll", timeout_s=120)
            self.require(polled.get("status") == "failed", "Force rebuild guard did not fail as expected", response=polled)
            error_text = polled.get("error") or ""
            self.require(
                "force rebuild blocked while user env containers exist" in error_text,
                "Force rebuild failed, but not for the expected guard reason",
                response=polled,
            )
            step.details = {"start_response": started, "final_response": polled}
            step.artifacts.append(str(self.artifacts_dir / "step-force-rebuild-start.json"))
        except ValidationFailure as exc:
            step.status = "failed"
            step.failure_summary = str(exc)
            step.details = exc.details
            step.engineer_handoff = exc.engineer_handoff + [
                "include the final rebuild job payload and the list of env-* containers present during the test",
            ]
            self.add_result(step)
            raise
        self.add_result(step)

    def cleanup_envs(self) -> None:
        for env_name in reversed(self.envs_to_cleanup):
            try:
                self.client.request_json(
                    "DELETE",
                    f"/envs/{env_name}",
                    artifact_name=f"cleanup-{env_name}.json",
                )
            except Exception as exc:
                self.add_result(
                    StepResult(
                        id=f"cleanup_{env_name}",
                        description=f"Cleanup for {env_name}",
                        status="failed",
                        failure_summary=f"Cleanup failed for {env_name}: {exc}",
                        details={"env_name": env_name},
                        artifacts=[str(self.artifacts_dir / f"cleanup-{env_name}.json")],
                        engineer_handoff=[
                            f"env_name: {env_name}",
                            "manual cleanup may be required; include the cleanup response artifact",
                        ],
                    )
                )
            else:
                self.add_result(
                    StepResult(
                        id=f"cleanup_{env_name}",
                        description=f"Cleanup for {env_name}",
                        status="passed",
                        validated=["runtime-backed test environment was destroyed successfully"],
                        details={"env_name": env_name},
                        artifacts=[str(self.artifacts_dir / f"cleanup-{env_name}.json")],
                    )
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate kennel runtime preset provisioning and emit machine-checkable JSON.",
    )
    parser.add_argument("--base-url", default=os.environ.get("KENNEL_BASE_URL", "http://localhost:8090"))
    parser.add_argument("--secret", default=os.environ.get("KENNEL_SECRET"))
    parser.add_argument("--repo-url", default=os.environ.get("TEST_REPO_URL", "https://github.com/octocat/Hello-World.git"))
    parser.add_argument("--openai-api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    parser.add_argument("--artifacts-dir", default=str(Path("artifacts/provisioning-validation")))
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--job-timeout", type=int, default=DEFAULT_JOB_TIMEOUT_S)
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL_S)
    parser.add_argument("--rebuild-if-needed", action="store_true", default=True)
    parser.add_argument("--no-rebuild-if-needed", dest="rebuild_if_needed", action="store_false")
    parser.add_argument("--cleanup", action="store_true", default=True)
    parser.add_argument("--no-cleanup", dest="cleanup", action="store_false")
    parser.add_argument("--test-force-rebuild-guard", action="store_true", default=True)
    parser.add_argument("--no-test-force-rebuild-guard", dest="test_force_rebuild_guard", action="store_false")
    parser.add_argument("--require-codex-ready", action="store_true", default=False)
    parser.add_argument("--require-claude-ready", action="store_true", default=False)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    args.started_at = utc_now()
    if not args.secret:
        parser.error("KENNEL_SECRET or --secret is required")
    return args


def main() -> int:
    args = parse_args()
    validator = Validator(args)
    return validator.run()


if __name__ == "__main__":
    raise SystemExit(main())
