from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace


KENNEL_SRC = Path(__file__).resolve().parents[1] / "src"
if str(KENNEL_SRC) not in sys.path:
    sys.path.insert(0, str(KENNEL_SRC))

import server


def test_hermes_bootstrap_profile_runtime_files_include_standard_paths() -> None:
    req = server.InjectRequest(user="dev", bootstrap_profile="hermes_agent_runtime")

    files = server._bootstrap_profile_runtime_files(req)

    assert "/home/dev/.hermes/config.yaml" in files
    assert "/home/dev/.hermes/.env" in files
    assert "/home/dev/.hermes/hermes-agent-launcher" in files
    assert files["/home/dev/.hermes/hermes-agent-launcher"].startswith("#!/usr/bin/env bash")
    assert (
        'DOG_WORKSPACE_AGENT_HERMES_RUNTIME_MODE="${DOG_WORKSPACE_AGENT_HERMES_RUNTIME_MODE:-gateway_ws}"'
        in files["/home/dev/.hermes/hermes-agent-launcher"]
    )
    assert 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:$PATH"' in files["/home/dev/.hermes/hermes-agent-launcher"]
    assert "DOG_WORKSPACE_AGENT_HERMES_PORT" in files["/home/dev/.hermes/hermes-agent-launcher"]
    assert "DOG_WORKSPACE_AGENT_HERMES_GATEWAY_CMD" in files["/home/dev/.hermes/hermes-agent-launcher"]
    assert "DOG_WORKSPACE_AGENT_HERMES_AUTO_INSTALL" in files["/home/dev/.hermes/hermes-agent-launcher"]
    assert "bash -s -- --skip-setup" in files["/home/dev/.hermes/hermes-agent-launcher"]
    assert "raw.githubusercontent.com is not resolvable" in files["/home/dev/.hermes/hermes-agent-launcher"]
    assert "API_SERVER_ENABLED=false" in files["/home/dev/.hermes/.env"]
    assert "API_SERVER_PORT=8642" in files["/home/dev/.hermes/.env"]


def test_hermes_service_defaults_are_websocket_gateway() -> None:
    profile = server.SERVICE_PROFILE_DEFAULTS["hermes"]

    assert profile.kind == "agent_runtime"
    assert profile.runtime_id == "hermes"
    assert profile.runtime_profile == "hermes_gateway_ws"
    assert profile.transport_kind == "websocket"
    assert profile.protocol == "ws"
    assert profile.port == 4319
    assert profile.path == "/"


def test_write_runtime_file_uses_restricted_mode_for_env_files(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_attach_exec(env_name: str, command: str, timeout: int = 30):
        captured["env_name"] = env_name
        captured["command"] = command
        captured["timeout"] = str(timeout)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(server, "_attach_exec", fake_attach_exec)

    result = server._write_runtime_file(
        "env-test",
        path="/home/dev/.hermes/.env",
        content="HERMES_API_KEY=xyz",
        user="dev",
    )

    assert result.returncode == 0
    assert "if [ -d /home/dev/.hermes/.env ]; then rm -rf /home/dev/.hermes/.env; fi" in captured["command"]
    assert "chmod 600 /home/dev/.hermes/.env" in captured["command"]


def test_write_runtime_file_marks_shebang_launchers_executable(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_attach_exec(env_name: str, command: str, timeout: int = 30):
        captured["env_name"] = env_name
        captured["command"] = command
        captured["timeout"] = str(timeout)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(server, "_attach_exec", fake_attach_exec)

    result = server._write_runtime_file(
        "env-test",
        path="/home/dev/.hermes/hermes-agent-launcher",
        content="#!/usr/bin/env bash\nexit 0\n",
        user="dev",
    )

    assert result.returncode == 0
    assert (
        "if [ -d /home/dev/.hermes/hermes-agent-launcher ]; then rm -rf /home/dev/.hermes/hermes-agent-launcher; fi"
        in captured["command"]
    )
    assert "chmod 755 /home/dev/.hermes/hermes-agent-launcher" in captured["command"]


def test_hermes_bootstrap_profile_uses_file_guard_for_launcher() -> None:
    req = server.InjectRequest(user="dev", bootstrap_profile="hermes_agent_runtime")

    plan = server._bootstrap_profile_plan(req)

    assert plan is not None
    start_step = plan.steps[-1]
    assert isinstance(start_step, server.BootstrapRunCommandStep)
    assert '[ -f "$HOME/.hermes/hermes-agent-launcher" ] && [ -x "$HOME/.hermes/hermes-agent-launcher" ]' in start_step.command


def test_hermes_readiness_message_points_to_runtime_log(monkeypatch) -> None:
    declared = server.SERVICE_PROFILE_DEFAULTS["hermes"]
    declared = declared.model_copy(
        update={
            "pid_path": "/tmp/hermes.pid",
            "port": 4319,
        }
    )

    monkeypatch.setattr(server, "_is_pid_running", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(server, "_is_port_listening", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(server, "_get_env_ipv4", lambda *_args, **_kwargs: "10.0.3.99")

    discovered = server._discover_service("env-hermes", declared)

    assert discovered.status == "pending"
    assert discovered.readiness_message is not None
    assert "4319" in discovered.readiness_message
    assert "/tmp/hermes.log" in discovered.readiness_message
