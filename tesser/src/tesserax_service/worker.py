from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import redis

from .contracts import RenderRequest
from .jobs import write_job_status_snapshot
from .redis_messages import (
    build_render_error_response,
    build_render_payload,
    build_render_response,
)
from .registry import get_script_spec
from .runtime import execute_render

REDIS_HOST = os.getenv("TESSER_REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("TESSER_REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("TESSER_REDIS_DB", "0"))


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _log(event: str, **fields: Any) -> None:
    payload = {"ts": _utc_now(), "event": event, **fields}
    print(json.dumps(payload), flush=True)


def _callback_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    callback = payload.get("callback")
    if isinstance(callback, dict):
        return callback
    return None


def _publish_callback(
    redis_client: redis.Redis,
    payload: dict[str, Any],
    response: dict[str, Any],
) -> None:
    callback = _callback_payload(payload)
    if not callback:
        return
    response_channel = callback.get("response_channel")
    if not isinstance(response_channel, str) or not response_channel:
        return
    redis_client.publish(response_channel, json.dumps(response))


def _process_job_file(
    payload: dict[str, Any],
    job_file: Path,
    archive_dir: Path,
    *,
    runtime_profile: str,
    default_timeout_seconds: float,
) -> tuple[RenderRequest, Any]:
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
    return request, result


def _job_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    meta = payload.get("job_metadata")
    if isinstance(meta, dict):
        return meta
    return {}


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
    worker_id = os.getenv("TESSER_WORKER_ID", f"tesser-worker-{args.runtime_profile}")
    jobs_dir = Path(args.jobs_root) / args.runtime_profile
    archive_dir = Path(args.jobs_root) / "archive" / args.runtime_profile
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )
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
            payload: dict[str, Any] = {}
            try:
                payload = json.loads(lock_file.read_text(encoding="utf-8"))
                request, result = _process_job_file(
                    payload,
                    lock_file,
                    archive_dir,
                    runtime_profile=args.runtime_profile,
                    default_timeout_seconds=args.default_timeout_seconds,
                )
                callback = _callback_payload(payload)
                if callback is not None:
                    spec = get_script_spec(request.script_id)
                    completed_at = _utc_now()
                    render = build_render_payload(result, spec)
                    response = build_render_response(
                        request_id=request.request_id,
                        room_id=(
                            str(callback.get("room_id"))
                            if callback.get("room_id") is not None
                            else None
                        ),
                        script_name=str(callback.get("script_name") or request.script_id),
                        worker_id=worker_id,
                        completed_at=completed_at,
                        render=render,
                        received_at=(
                            str(callback.get("received_at"))
                            if callback.get("received_at") is not None
                            else None
                        ),
                    )
                    _publish_callback(redis_client, payload, response)
                else:
                    completed_at = _utc_now()
                    render = build_render_payload(result, get_script_spec(request.script_id))

                meta = _job_metadata(payload)
                write_job_status_snapshot(
                    args.jobs_root,
                    args.runtime_profile,
                    str(request.request_id or lock_file.stem),
                    {
                        "job_id": str(request.request_id or lock_file.stem),
                        "script_name": str(meta.get("script_name") or request.script_id),
                        "room_id": (
                            str(meta.get("room_id")) if meta.get("room_id") is not None else None
                        ),
                        "status": "completed",
                        "worker_id": worker_id,
                        "runtime_profile": args.runtime_profile,
                        "resolved_capabilities": result.resolved_capabilities,
                        "queued_at": (
                            str(meta.get("queued_at")) if meta.get("queued_at") is not None else None
                        ),
                        "completed_at": completed_at,
                        "render": render,
                    },
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
                callback = _callback_payload(payload)
                if callback is not None:
                    completed_at = _utc_now()
                    _publish_callback(
                        redis_client,
                        payload,
                        build_render_error_response(
                            request_id=(
                                str(payload.get("request_id"))
                                if payload.get("request_id") is not None
                                else None
                            ),
                            room_id=(
                                str(callback.get("room_id"))
                                if callback.get("room_id") is not None
                                else None
                            ),
                            script_name=(
                                str(callback.get("script_name") or payload.get("script_id"))
                                if callback.get("script_name") is not None
                                or payload.get("script_id") is not None
                                else None
                            ),
                            worker_id=worker_id,
                            completed_at=completed_at,
                            error=str(exc),
                            received_at=(
                                str(callback.get("received_at"))
                                if callback.get("received_at") is not None
                                else None
                            ),
                        ),
                    )
                else:
                    completed_at = _utc_now()
                meta = _job_metadata(payload)
                write_job_status_snapshot(
                    args.jobs_root,
                    args.runtime_profile,
                    str(payload.get("request_id") or lock_file.stem),
                    {
                        "job_id": str(payload.get("request_id") or lock_file.stem),
                        "script_name": str(meta.get("script_name") or payload.get("script_id") or ""),
                        "room_id": (
                            str(meta.get("room_id")) if meta.get("room_id") is not None else None
                        ),
                        "status": "error",
                        "worker_id": worker_id,
                        "runtime_profile": args.runtime_profile,
                        "resolved_capabilities": payload.get("resolved_capabilities", []),
                        "queued_at": (
                            str(meta.get("queued_at")) if meta.get("queued_at") is not None else None
                        ),
                        "completed_at": completed_at,
                        "error": str(exc),
                    },
                )
                lock_file.unlink(missing_ok=True)

        if args.once:
            break
        if not processed:
            time.sleep(args.poll_seconds)
    redis_client.close()


if __name__ == "__main__":
    main()
