from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .contracts import RenderRequest
from .runtime import execute_render


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _log(event: str, **fields: Any) -> None:
    payload = {"ts": _utc_now(), "event": event, **fields}
    print(json.dumps(payload), flush=True)


def _process_job_file(
    job_file: Path,
    archive_dir: Path,
    *,
    runtime_profile: str,
    default_timeout_seconds: float,
) -> None:
    payload = json.loads(job_file.read_text(encoding="utf-8"))
    payload_params = payload.get("params", {})
    if not isinstance(payload_params, dict):
        raise ValueError("job params must be an object")
    payload_params.setdefault("__timeout_seconds", default_timeout_seconds)
    payload["params"] = payload_params

    request = RenderRequest.from_dict(payload)
    started_at = time.perf_counter()
    _log(
        "job_started",
        script_id=request.script_id,
        request_id=request.request_id,
        runtime_profile=runtime_profile,
        job_file=str(job_file),
    )
    result = execute_render(request)
    duration = round(time.perf_counter() - started_at, 4)

    result_path = archive_dir / f"{job_file.stem}.result.json"
    result_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    _log(
        "job_completed",
        script_id=request.script_id,
        request_id=request.request_id,
        runtime_profile=runtime_profile,
        duration_seconds=duration,
        result_path=str(result_path),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the tesserax render worker")
    parser.add_argument("--jobs-root", default=".jobs")
    parser.add_argument("--runtime-profile", choices=["core", "export"], default="core")
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--default-timeout-seconds", type=float, default=300.0)
    parser.add_argument("--once", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    jobs_dir = Path(args.jobs_root) / args.runtime_profile
    archive_dir = Path(args.jobs_root) / "archive" / args.runtime_profile
    jobs_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    _log(
        "worker_started",
        jobs_dir=str(jobs_dir),
        archive_dir=str(archive_dir),
        runtime_profile=args.runtime_profile,
        poll_seconds=args.poll_seconds,
        default_timeout_seconds=args.default_timeout_seconds,
    )

    while True:
        processed = False
        for job_file in sorted(jobs_dir.glob("*.json")):
            lock_file = job_file.with_suffix(".processing")
            try:
                job_file.rename(lock_file)
            except FileNotFoundError:
                continue
            except OSError:
                continue

            processed = True
            try:
                _process_job_file(
                    lock_file,
                    archive_dir,
                    runtime_profile=args.runtime_profile,
                    default_timeout_seconds=args.default_timeout_seconds,
                )
                lock_file.rename(archive_dir / f"{lock_file.stem}.done.json")
            except Exception as exc:  # noqa: BLE001
                fail_path = archive_dir / f"{lock_file.stem}.failed.json"
                error_payload = {
                    "status": "failed",
                    "error": str(exc),
                    "runtime_profile": args.runtime_profile,
                }
                fail_path.write_text(
                    json.dumps(error_payload, indent=2), encoding="utf-8"
                )
                _log(
                    "job_failed",
                    runtime_profile=args.runtime_profile,
                    job_file=str(lock_file),
                    error=str(exc),
                    failed_path=str(fail_path),
                )
                lock_file.unlink(missing_ok=True)

        if args.once:
            break
        if not processed:
            time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
