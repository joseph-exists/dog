from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .contracts import RenderRequest
from .jobs import enqueue_render_job
from .registry import list_script_specs
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

            queued = enqueue_render_job(request, self.jobs_root)
            self._send_json(
                202,
                {
                    "job_id": queued["request_id"],
                    "job_path": queued["job_path"],
                    "runtime_profile": queued["runtime_profile"],
                    "resolved_capabilities": queued["resolved_capabilities"],
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
