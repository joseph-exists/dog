from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import RenderRequest
from .jobs import enqueue_render_job
from .profiles import explain_profile
from .registry import list_script_specs
from .runtime import execute_render
from . import scripts as _scripts  # noqa: F401


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tesserax service CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_cmd = subparsers.add_parser("list-scripts", help="List registered script IDs")
    list_cmd.add_argument("--json", action="store_true")

    render = subparsers.add_parser("render", help="Run a render synchronously")
    render.add_argument("--script-id", required=True)
    render.add_argument("--params-json", default="{}")
    render.add_argument("--output-dir", default="artifacts")
    render.add_argument("--formats", default="svg")
    render.add_argument("--basename", default="render")
    render.add_argument("--request-id")
    render.add_argument("--runtime-profile", choices=["core", "export"], default=None)
    render.add_argument("--timeout-seconds", type=float, default=None)

    submit = subparsers.add_parser(
        "submit-job", help="Submit a render job file for the worker"
    )
    submit.add_argument("--script-id", required=True)
    submit.add_argument("--params-json", default="{}")
    submit.add_argument("--output-dir", default="artifacts")
    submit.add_argument("--formats", default="svg")
    submit.add_argument("--basename", default="render")
    submit.add_argument("--request-id")
    submit.add_argument("--runtime-profile", choices=["core", "export"], default=None)
    submit.add_argument("--timeout-seconds", type=float, default=None)
    submit.add_argument("--jobs-root", default=".jobs")

    return parser


def _parse_request(args: argparse.Namespace) -> RenderRequest:
    params = json.loads(args.params_json)
    if not isinstance(params, dict):
        raise ValueError("--params-json must decode to an object")
    if args.timeout_seconds is not None:
        params["__timeout_seconds"] = args.timeout_seconds

    return RenderRequest(
        script_id=args.script_id,
        params=params,
        output_dir=args.output_dir,
        formats=[fmt.strip() for fmt in args.formats.split(",") if fmt.strip()],
        basename=args.basename,
        request_id=args.request_id,
        runtime_profile=args.runtime_profile,
    )


def _handle_render(args: argparse.Namespace) -> None:
    request = _parse_request(args)
    result = execute_render(request)
    print(json.dumps(result.to_dict(), indent=2))


def _handle_submit_job(args: argparse.Namespace) -> None:
    request = _parse_request(args)
    queued = enqueue_render_job(request, Path(args.jobs_root))
    response = {
        "job_path": queued["job_path"],
        "runtime_profile": queued["runtime_profile"],
        "resolved_capabilities": queued["resolved_capabilities"],
    }
    print(json.dumps(response, indent=2))


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "list-scripts":
        specs = list_script_specs()
        if args.json:
            print(json.dumps([spec.to_dict() for spec in specs], indent=2))
            return
        for spec in specs:
            profile_info = explain_profile(spec.default_runtime_profile)
            print(
                f"{spec.script_id}\t{spec.kind}\t{profile_info['profile']}\t"
                f"{'enabled' if spec.enabled else 'disabled'}"
            )
        return
    if args.command == "render":
        _handle_render(args)
        return
    if args.command == "submit-job":
        _handle_submit_job(args)
        return
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
