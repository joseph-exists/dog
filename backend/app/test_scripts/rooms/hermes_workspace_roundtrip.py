#!/usr/bin/env python3
"""
Provision a Hermes workspace, attach it to a room, and validate one round trip.

This module is intentionally structured so it can be used both as a standalone
test script and as the implementation behind a Typer command.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any

import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))
from auth_helper import AuthHelper, AuthenticationError

DEFAULT_BASE_URL = "http://api.localhost:8000"
DEFAULT_OUTPUT_FILE = Path(__file__).with_name("test_results_hermes_workspace_roundtrip.json")
CANONICAL_WORKSPACE_PATH = "/home/dev/workspace"
CANONICAL_HERMES_HOME = "/home/dev/.hermes"


class HermesWorkspaceRoundTripError(RuntimeError):
    """Raised when the Hermes room/runtime validation flow fails."""


@dataclass(slots=True)
class HermesWorkspaceRoundTripConfig:
    base_url: str = DEFAULT_BASE_URL
    workspace_name: str = "Hermes API Validation Workspace"
    room_title: str = "Hermes API Validation Room"
    prompt: str = (
        "Reply with exactly: HERMES_ROOM_RUNTIME_OK. "
        "Do not add any other words."
    )
    timeout_seconds: int = 240
    poll_interval_seconds: float = 3.0
    cleanup: bool = False
    output_file: Path | None = DEFAULT_OUTPUT_FILE


def _api_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/api/v1{path}"


def _request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    expected_statuses: tuple[int, ...] = (200,),
    **kwargs: Any,
) -> Any:
    response = session.request(method, url, **kwargs)
    if response.status_code not in expected_statuses:
        detail = response.text.strip()
        raise HermesWorkspaceRoundTripError(
            f"{method} {url} failed with HTTP {response.status_code}: {detail}"
        )
    if not response.content:
        return None
    return response.json()


def _get_authenticated_session(base_url: str) -> requests.Session:
    helper = AuthHelper()
    login_response = requests.post(
        _api_url(base_url, "/login/access-token"),
        data={
            "username": helper.test_email,
            "password": helper.test_password,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if login_response.status_code != 200:
        raise AuthenticationError(
            f"Authentication failed with HTTP {login_response.status_code}: {login_response.text}"
        )
    token = login_response.json()["access_token"]
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    )
    return session


def _find_hermes_runtime_service(workspace: dict[str, Any]) -> dict[str, Any] | None:
    services = workspace.get("services") or []
    for service in services:
        if (
            service.get("runtime_id") == "hermes"
            and service.get("runtime_profile") == "hermes_api_server"
        ):
            return service
    return None


def _wait_for_workspace_service_ready(
    session: requests.Session,
    *,
    config: HermesWorkspaceRoundTripConfig,
    workspace_id: str,
) -> dict[str, Any]:
    deadline = time.monotonic() + config.timeout_seconds
    last_workspace: dict[str, Any] | None = None
    last_message = "Hermes API service has not been discovered yet."

    while time.monotonic() < deadline:
        workspace = _request_json(
            session,
            "GET",
            _api_url(config.base_url, f"/workspaces/{workspace_id}"),
        )
        last_workspace = workspace
        hermes_service = _find_hermes_runtime_service(workspace)

        if hermes_service is not None:
            service_status = hermes_service.get("status")
            last_message = hermes_service.get("readiness_message") or (
                f"Hermes service status is {service_status}."
            )
            if service_status == "ready":
                return workspace
        else:
            last_message = "Hermes API service is still missing from workspace services."

        time.sleep(config.poll_interval_seconds)

    workspace_status = (last_workspace or {}).get("status")
    raise HermesWorkspaceRoundTripError(
        "Timed out waiting for Hermes API service readiness. "
        f"workspace_status={workspace_status!r}; detail={last_message}"
    )


def _wait_for_runtime_descriptor(
    session: requests.Session,
    *,
    config: HermesWorkspaceRoundTripConfig,
    room_id: str,
    workspace_id: str,
) -> dict[str, Any]:
    deadline = time.monotonic() + config.timeout_seconds
    last_descriptor: dict[str, Any] | None = None

    while time.monotonic() < deadline:
        descriptor = _request_json(
            session,
            "POST",
            _api_url(config.base_url, f"/rooms/{room_id}/workspace-connections"),
            expected_statuses=(200, 201),
            json={
                "workspace_id": workspace_id,
                "purpose": "agent_runtime_connect",
            },
        )
        last_descriptor = descriptor
        if descriptor.get("status") == "available" and descriptor.get("endpoints"):
            return descriptor
        time.sleep(config.poll_interval_seconds)

    raise HermesWorkspaceRoundTripError(
        "Timed out waiting for a room runtime descriptor backed by the Hermes API service. "
        f"last_descriptor={json.dumps(last_descriptor or {}, indent=2)}"
    )


def _cleanup_resource(
    session: requests.Session,
    *,
    config: HermesWorkspaceRoundTripConfig,
    path: str,
) -> None:
    response = session.delete(_api_url(config.base_url, path))
    if response.status_code not in (200, 204, 404):
        raise HermesWorkspaceRoundTripError(
            f"Cleanup failed for {path}: HTTP {response.status_code} {response.text}"
        )


def run_hermes_workspace_roundtrip(
    config: HermesWorkspaceRoundTripConfig,
    *,
    verbose: bool = True,
) -> dict[str, Any]:
    session = _get_authenticated_session(config.base_url)

    created_workspace_id: str | None = None
    created_room_id: str | None = None

    def log(message: str) -> None:
        if verbose:
            print(message)

    started_at = datetime.now(timezone.utc)

    try:
        log("Creating Hermes workspace...")
        workspace = _request_json(
            session,
            "POST",
            _api_url(config.base_url, "/workspaces/"),
            expected_statuses=(200, 201, 202),
            json={
                "name": config.workspace_name,
                "flavour": "dev",
                "kind": "ephemeral",
                "runtime_preset": "hermes",
                "bootstrap": {
                    "workspace_path": CANONICAL_WORKSPACE_PATH,
                    "startup_intent": {
                        "mode": "agent_service",
                        "agent_profile": "hermes",
                    },
                    "bootstrap_profile": "hermes_api_server",
                    "runtime_files": {},
                    "env_vars": {},
                },
            },
        )
        created_workspace_id = workspace["id"]

        log("Creating room...")
        room = _request_json(
            session,
            "POST",
            _api_url(config.base_url, "/rooms"),
            expected_statuses=(200, 201),
            json={"title": config.room_title},
        )
        created_room_id = room["room_id"]

        log("Waiting for Hermes API service readiness...")
        ready_workspace = _wait_for_workspace_service_ready(
            session,
            config=config,
            workspace_id=created_workspace_id,
        )
        ready_service = _find_hermes_runtime_service(ready_workspace)
        assert ready_service is not None

        log("Waiting for room/runtime descriptor availability...")
        descriptor = _wait_for_runtime_descriptor(
            session,
            config=config,
            room_id=created_room_id,
            workspace_id=created_workspace_id,
        )

        log("Attaching workspace to room...")
        current_connection = _request_json(
            session,
            "PUT",
            _api_url(config.base_url, f"/rooms/{created_room_id}/workspace-connections/current"),
            expected_statuses=(200, 201),
            json={
                "workspace_id": created_workspace_id,
                "purpose": "agent_runtime_connect",
            },
        )
        if current_connection.get("state") != "active":
            raise HermesWorkspaceRoundTripError(
                "Room workspace connection did not become active: "
                f"{json.dumps(current_connection, indent=2)}"
            )

        log("Invoking Hermes room runtime...")
        invocation = _request_json(
            session,
            "POST",
            _api_url(config.base_url, f"/rooms/{created_room_id}/workspace-runtime/invoke"),
            expected_statuses=(200, 201),
            json={"input": config.prompt},
        )
        output_text = (invocation.get("output_text") or "").strip()
        if not output_text:
            raise HermesWorkspaceRoundTripError(
                f"Hermes runtime returned empty output: {json.dumps(invocation, indent=2)}"
            )

        log("Verifying emitted room message...")
        messages = _request_json(
            session,
            "GET",
            _api_url(config.base_url, f"/rooms/{created_room_id}/messages"),
            expected_statuses=(200,),
            params={"limit": 20},
        )
        runtime_message = next(
            (
                message
                for message in messages.get("data", [])
                if message.get("message_id") == invocation.get("message_id")
            ),
            None,
        )
        if runtime_message is None:
            raise HermesWorkspaceRoundTripError(
                "Invocation succeeded but the emitted room message was not found."
            )

        completed_at = datetime.now(timezone.utc)
        result = {
            "status": "passed",
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": (completed_at - started_at).total_seconds(),
            "workspace": {
                "id": created_workspace_id,
                "name": ready_workspace.get("name"),
                "status": ready_workspace.get("status"),
                "bootstrap_profile": (
                    ((ready_workspace.get("bootstrap") or {}).get("intent") or {}).get("bootstrap_profile")
                ),
                "service": ready_service,
                "canonical_paths": {
                    "workspace_path": CANONICAL_WORKSPACE_PATH,
                    "hermes_home": CANONICAL_HERMES_HOME,
                },
            },
            "room": {
                "id": created_room_id,
                "title": room.get("title"),
            },
            "descriptor": descriptor,
            "current_connection": current_connection,
            "invocation": invocation,
            "runtime_message": runtime_message,
        }
        if config.output_file is not None:
            config.output_file.write_text(json.dumps(result, indent=2) + "\n")
        return result
    finally:
        if config.cleanup:
            if created_room_id:
                log("Cleaning up room...")
                _cleanup_resource(
                    session,
                    config=config,
                    path=f"/rooms/{created_room_id}",
                )
            if created_workspace_id:
                log("Cleaning up workspace...")
                _cleanup_resource(
                    session,
                    config=config,
                    path=f"/workspaces/{created_workspace_id}",
                )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Provision a Hermes workspace, attach it to a room, and validate one "
            "message round trip through the room workspace runtime."
        )
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--workspace-name", default="Hermes API Validation Workspace")
    parser.add_argument("--room-title", default="Hermes API Validation Room")
    parser.add_argument(
        "--prompt",
        default="Reply with exactly: HERMES_ROOM_RUNTIME_OK. Do not add any other words.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=240)
    parser.add_argument("--poll-interval-seconds", type=float, default=3.0)
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--output-file",
        default=str(DEFAULT_OUTPUT_FILE),
        help="Where to write the structured JSON result. Use 'none' to disable.",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    output_file = None if str(args.output_file).lower() == "none" else Path(args.output_file)
    config = HermesWorkspaceRoundTripConfig(
        base_url=args.base_url,
        workspace_name=args.workspace_name,
        room_title=args.room_title,
        prompt=args.prompt,
        timeout_seconds=args.timeout_seconds,
        poll_interval_seconds=args.poll_interval_seconds,
        cleanup=args.cleanup,
        output_file=output_file,
    )
    try:
        result = run_hermes_workspace_roundtrip(config, verbose=not args.quiet)
    except (AuthenticationError, HermesWorkspaceRoundTripError, requests.RequestException) as exc:
        failure = {
            "status": "failed",
            "error": str(exc),
            "config": {
                **asdict(config),
                "output_file": str(config.output_file) if config.output_file else None,
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if output_file is not None:
            output_file.write_text(json.dumps(failure, indent=2) + "\n")
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
