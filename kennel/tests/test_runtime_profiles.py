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
    assert "/home/dev/.hermes/hermes-agent" in files
    assert files["/home/dev/.hermes/hermes-agent"].startswith("#!/usr/bin/env bash")


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
        path="/home/dev/.hermes/hermes-agent",
        content="#!/usr/bin/env bash\nexit 0\n",
        user="dev",
    )

    assert result.returncode == 0
    assert "chmod 755 /home/dev/.hermes/hermes-agent" in captured["command"]
