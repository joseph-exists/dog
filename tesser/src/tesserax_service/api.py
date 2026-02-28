from __future__ import annotations

import argparse
import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .contracts import RenderRequest
from .profiles import resolve_capabilities, runtime_profile_for_capabilities
from .registry import get_script_spec, list_script_specs
from .runtime import execute_render
from . import scripts as _scripts  # noqa: F401


class RenderRequestHandler(BaseHTTPRequestHandler):
    server_version = "tesserax-service/0"
    jobs_root = Path(".jobs")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/v1/scripts":
            self._send_json(
                200,
                {"scripts": [spec.to_dict() for spec in list_script_specs()]},
            )
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/v1/renders", "/v1/jobs"}:
            self._send_json(404, {"error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_payload = self.rfile.read(length)
            payload = json.loads(raw_payload.decode("utf-8"))
            timeout_seconds = payload.pop("timeout_seconds", None)
            if timeout_seconds is not None:
                if not isinstance(payload.get("params"), dict):
                    payload["params"] = {}
                payload["params"]["__timeout_seconds"] = timeout_seconds
            request = RenderRequest.from_dict(payload)
            if self.path == "/v1/renders":
                result = execute_render(request)
                self._send_json(200, result.to_dict())
                return

            spec = get_script_spec(request.script_id)
            capabilities = resolve_capabilities(spec, request)
            resolved_profile = runtime_profile_for_capabilities(
                capabilities, default_profile=spec.default_runtime_profile
            )
            if request.runtime_profile is not None and request.runtime_profile != resolved_profile:
                raise RuntimeError(
                    f"runtime_profile mismatch: requested='{request.runtime_profile}' "
                    f"resolved='{resolved_profile}'"
                )

            request_id = request.request_id or str(uuid.uuid4())
            jobs_dir = self.jobs_root / resolved_profile
            jobs_dir.mkdir(parents=True, exist_ok=True)
            job_path = jobs_dir / f"{request_id}.json"
            job_payload = {
                "script_id": request.script_id,
                "params": request.params,
                "output_dir": request.output_dir,
                "formats": request.formats,
                "basename": request.basename,
                "request_id": request_id,
                "runtime_profile": resolved_profile,
            }
            job_path.write_text(json.dumps(job_payload, indent=2), encoding="utf-8")
            self._send_json(
                202,
                {
                    "job_id": request_id,
                    "job_path": str(job_path),
                    "runtime_profile": resolved_profile,
                    "resolved_capabilities": sorted(capabilities),
                },
            )
        except Exception as exc:  # noqa: BLE001
            self._send_json(400, {"error": str(exc)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the tesserax sync render API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--jobs-root", default=".jobs")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    RenderRequestHandler.jobs_root = Path(args.jobs_root)
    server = ThreadingHTTPServer((args.host, args.port), RenderRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
