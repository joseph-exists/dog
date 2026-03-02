from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tesserax_service.registry import register_script

_SCRIPT_ROOT = Path(__file__).resolve().parent
_EXAMPLES_ROOT = _SCRIPT_ROOT / "examples_other"
_SRC_ROOT = _SCRIPT_ROOT.parents[1]
_MANIFEST_PATH = _EXAMPLES_ROOT / "examples_manifest.yaml"

_EXPORT_FORMATS = {"gif", "mp4", "png", "pdf", "ps"}
_MEDIA_SUFFIXES = {".svg", ".gif", ".mp4", ".png", ".pdf", ".ps", ".json", ".csv"}
_RESERVED_PARAMS = {"argv", "timeout_seconds", "__timeout_seconds", "capture_logs", "__capture_logs"}
_DEFAULT_TIMEOUT_SECONDS = 300.0


@dataclass(slots=True)
class ExternalScriptSpec:
    script_id: str
    rel_path: str
    kind: str
    supports_output: bool
    supports_output_prefix: bool
    supports_format: bool
    supported_formats: list[str]
    default_runtime_profile: str
    enabled: bool
    disabled_reason: str | None

    def to_manifest_entry(self) -> dict[str, Any]:
        return {
            "script_id": self.script_id,
            "rel_path": self.rel_path,
            "kind": self.kind,
            "supports_output": self.supports_output,
            "supports_output_prefix": self.supports_output_prefix,
            "supports_format": self.supports_format,
            "supported_formats": self.supported_formats,
            "default_runtime_profile": self.default_runtime_profile,
            "enabled": self.enabled,
            "disabled_reason": self.disabled_reason,
        }


def _parse_manifest_kinds(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    kinds: dict[str, str] = {}
    current_path: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- path:"):
            current_path = line.split(":", 1)[1].strip()
            if current_path.startswith("examples-other/"):
                current_path = current_path[len("examples-other/") :]
            continue
        if line.startswith("kind:") and current_path is not None:
            kinds[current_path] = line.split(":", 1)[1].strip()
            current_path = None
    return kinds


def _infer_formats(text: str, kind: str) -> list[str]:
    found: list[str] = []
    for fmt in ("svg", "gif", "mp4", "png", "pdf", "ps"):
        if f'"{fmt}"' in text or f"'{fmt}'" in text:
            found.append(fmt)
    if found:
        dedup: list[str] = []
        for fmt in found:
            if fmt not in dedup:
                dedup.append(fmt)
        return dedup
    if "--format" in text:
        return ["gif"] if kind == "animation" else ["svg"]
    if kind == "animation":
        return ["gif"]
    if kind == "static":
        return ["svg"]
    return []


def _infer_kind(rel_path: str, manifest_kinds: dict[str, str]) -> str:
    if rel_path in manifest_kinds:
        return manifest_kinds[rel_path]
    if rel_path.endswith("_runner.py"):
        return "runner"
    if rel_path in {"run_full_suite_for_review.py", "validate_parameter_parity.py"}:
        return "utility"
    if rel_path.startswith("animation/"):
        return "animation"
    if rel_path.startswith("static/"):
        return "static"
    if rel_path.startswith("data/"):
        return "utility"
    return "utility"


def _classify_spec(rel_path: str, text: str, kind: str) -> ExternalScriptSpec:
    script_id = f"examples.{rel_path[:-3].replace('/', '.')}"
    supports_output = "--output" in text
    supports_output_prefix = "--output-prefix" in text
    supports_format = "--format" in text
    supported_formats = _infer_formats(text, kind)

    has_core_mode = "svg" in supported_formats
    default_profile = "core" if has_core_mode else "export"

    enabled = kind in {"static", "animation"}
    disabled_reason = None
    if kind not in {"static", "animation"}:
        disabled_reason = "Utility/runner scripts are not enabled as render jobs"

    return ExternalScriptSpec(
        script_id=script_id,
        rel_path=rel_path,
        kind=kind,
        supports_output=supports_output,
        supports_output_prefix=supports_output_prefix,
        supports_format=supports_format,
        supported_formats=supported_formats,
        default_runtime_profile=default_profile,
        enabled=enabled,
        disabled_reason=disabled_reason,
    )


def build_first_pass_catalog() -> list[ExternalScriptSpec]:
    manifest_kinds = _parse_manifest_kinds(_MANIFEST_PATH)
    specs: list[ExternalScriptSpec] = []
    for path in sorted(_EXAMPLES_ROOT.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        rel_path = path.relative_to(_EXAMPLES_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        kind = _infer_kind(rel_path, manifest_kinds)
        specs.append(_classify_spec(rel_path, text, kind))
    return specs


def _build_command(
    spec: ExternalScriptSpec,
    script_path: Path,
    params: dict[str, Any],
    output_dir: Path,
    basename: str,
    formats: list[str],
) -> tuple[list[str], Path | None]:
    requested_format = formats[0].lower() if formats else None
    if requested_format and spec.supported_formats and requested_format not in spec.supported_formats:
        raise RuntimeError(
            f"Unsupported format '{requested_format}' for script '{spec.script_id}'. "
            f"Supported: {', '.join(spec.supported_formats)}"
        )
    chosen_format = requested_format or (spec.supported_formats[0] if spec.supported_formats else None)
    cmd = [sys.executable, str(script_path)]
    expected_primary: Path | None = None

    if spec.supports_output_prefix:
        cmd.extend(["--output-prefix", str(output_dir / basename)])
    elif spec.supports_output:
        extension = chosen_format or "txt"
        expected_primary = output_dir / f"{basename}.{extension}"
        cmd.extend(["--output", str(expected_primary)])

    if spec.supports_format and chosen_format is not None:
        cmd.extend(["--format", chosen_format])

    argv = params.get("argv")
    if argv is not None:
        if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
            raise ValueError("params.argv must be a list of strings")
        cmd.extend(argv)
    else:
        for key, value in params.items():
            if key in _RESERVED_PARAMS:
                continue
            flag = f"--{key.replace('_', '-')}"
            if isinstance(value, bool):
                if value:
                    cmd.append(flag)
                continue
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                for item in value:
                    cmd.extend([flag, str(item)])
                continue
            cmd.extend([flag, str(value)])

    return cmd, expected_primary


def _resolve_timeout_seconds(params: dict[str, Any]) -> float:
    raw = params.get("__timeout_seconds", params.get("timeout_seconds", _DEFAULT_TIMEOUT_SECONDS))
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("timeout_seconds must be numeric") from exc
    if timeout <= 0:
        raise ValueError("timeout_seconds must be > 0")
    return timeout


def _resolve_capture_logs(params: dict[str, Any]) -> bool:
    raw = params.get("__capture_logs", params.get("capture_logs", True))
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.lower() in {"1", "true", "yes", "on"}
    return bool(raw)


def _artifact_delta(output_dir: Path, started_at: float, expected_primary: Path | None) -> list[Path]:
    artifacts = [
        path
        for path in output_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in _MEDIA_SUFFIXES
        and path.stat().st_mtime >= started_at - 0.01
    ]
    if not artifacts and expected_primary is not None and expected_primary.exists():
        artifacts = [expected_primary]
    return sorted(set(artifacts))


def _base_capabilities(spec: ExternalScriptSpec) -> set[str]:
    caps: set[str] = set()
    if spec.kind == "utility":
        caps.add("script.utility")
    if spec.kind == "runner":
        caps.add("script.runner")
    return caps


def _register_external(spec: ExternalScriptSpec) -> None:
    script_path = _EXAMPLES_ROOT / spec.rel_path

    @register_script(
        spec.script_id,
        kind=spec.kind,
        default_runtime_profile=spec.default_runtime_profile,
        enabled=spec.enabled,
        disabled_reason=spec.disabled_reason,
        base_capabilities=_base_capabilities(spec),
    )
    def _run(
        params: dict[str, Any], output_dir: Path, basename: str, formats: list[str]
    ) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        timeout_seconds = _resolve_timeout_seconds(params)
        capture_logs = _resolve_capture_logs(params)
        cmd, expected_primary = _build_command(
            spec=spec,
            script_path=script_path,
            params=params,
            output_dir=output_dir,
            basename=basename,
            formats=formats,
        )

        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{_SRC_ROOT}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(_SRC_ROOT)
        )
        started_at = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=output_dir,
                text=True,
                capture_output=True,
                env=env,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            if capture_logs:
                stdout = exc.stdout if isinstance(exc.stdout, str) else ""
                stderr = exc.stderr if isinstance(exc.stderr, str) else ""
                (output_dir / f"{basename}.stdout.log").write_text(stdout, encoding="utf-8")
                (output_dir / f"{basename}.stderr.log").write_text(stderr, encoding="utf-8")
                meta = {
                    "script_id": spec.script_id,
                    "command": cmd,
                    "returncode": None,
                    "duration_seconds": round(time.time() - started_at, 4),
                    "timeout_seconds": timeout_seconds,
                    "timed_out": True,
                }
                (output_dir / f"{basename}.run.json").write_text(
                    json.dumps(meta, indent=2), encoding="utf-8"
                )
            raise RuntimeError(
                f"Script '{spec.script_id}' exceeded timeout of {timeout_seconds:.1f}s"
            ) from exc

        if capture_logs:
            (output_dir / f"{basename}.stdout.log").write_text(
                proc.stdout or "", encoding="utf-8"
            )
            (output_dir / f"{basename}.stderr.log").write_text(
                proc.stderr or "", encoding="utf-8"
            )

            meta = {
                "script_id": spec.script_id,
                "command": cmd,
                "returncode": proc.returncode,
                "duration_seconds": round(time.time() - started_at, 4),
                "timeout_seconds": timeout_seconds,
                "timed_out": False,
            }
            (output_dir / f"{basename}.run.json").write_text(
                json.dumps(meta, indent=2), encoding="utf-8"
            )
        if proc.returncode != 0:
            stderr_tail = (proc.stderr or "").strip().splitlines()[-10:]
            raise RuntimeError(
                f"Script '{spec.script_id}' failed with exit code {proc.returncode}: "
                + " | ".join(stderr_tail)
            )

        artifacts = _artifact_delta(output_dir, started_at, expected_primary)
        if not artifacts:
            raise RuntimeError(
                f"Script '{spec.script_id}' completed but produced no detectable artifacts"
            )
        return artifacts


def register_external_examples() -> None:
    for spec in build_first_pass_catalog():
        _register_external(spec)


def write_first_pass_manifest(path: Path) -> None:
    payload = [spec.to_manifest_entry() for spec in build_first_pass_catalog()]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
