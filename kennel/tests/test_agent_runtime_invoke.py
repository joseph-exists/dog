from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


KENNEL_SRC = Path(__file__).resolve().parents[1] / "src"
if str(KENNEL_SRC) not in sys.path:
    sys.path.insert(0, str(KENNEL_SRC))

import server


def _declared_runtime_service(
    *,
    service_id: str = "codex",
    runtime_id: str = "codex",
    runtime_profile: str | None = "codex_app_server",
    transport_kind: str | None = "websocket",
    workspace_path: str | None = "/home/dev/workspace",
    protocol: str = "ws",
) -> server.DeclaredWorkspaceService:
    return server.DeclaredWorkspaceService(
        id=service_id,
        service_name=service_id,
        label="Runtime",
        kind="agent_runtime",
        runtime_id=runtime_id,
        runtime_profile=runtime_profile,
        transport_kind=transport_kind,
        protocol=protocol,
        port=4500,
        path="/",
        workspace_path=workspace_path,
    )


def _discovered_runtime_service(
    *,
    service_id: str = "codex",
    runtime_id: str = "codex",
    runtime_profile: str | None = "codex_app_server",
    transport_kind: str | None = "websocket",
    status: str = "ready",
    protocol: str = "ws",
) -> server.DiscoveredWorkspaceService:
    return server.DiscoveredWorkspaceService(
        id=service_id,
        service_name=service_id,
        label="Runtime",
        kind="agent_runtime",
        runtime_id=runtime_id,
        runtime_profile=runtime_profile,
        transport_kind=transport_kind,
        status=status,
        protocol=protocol,
        host="10.0.3.22",
        port=4500,
        path="/",
        url=f"{protocol}://10.0.3.22:4500/",
    )


@pytest.mark.asyncio
async def test_invoke_agent_runtime_uses_websocket_path(monkeypatch: pytest.MonkeyPatch) -> None:
    declared = _declared_runtime_service()
    discovered = _discovered_runtime_service()

    monkeypatch.setattr(
        server,
        "lxc",
        lambda *args: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(server, "_read_service_manifest", lambda name: [declared])
    monkeypatch.setattr(server, "_discover_service", lambda name, service: discovered)

    async def fake_invoke_agent_runtime_websocket(*, service, payload, timeout_seconds):
        assert service == discovered
        assert payload == {"type": "room.workspace.runtime.invoke"}
        assert timeout_seconds == 21.0
        return {
            "status": "completed",
            "transport_kind": "websocket",
            "protocol": "ws",
            "response": {"success": True, "output_text": "Codex websocket reply."},
        }

    monkeypatch.setattr(
        server,
        "_invoke_agent_runtime_websocket",
        fake_invoke_agent_runtime_websocket,
    )

    response = await server.invoke_agent_runtime(
        name="env-runtime",
        service_id="codex",
        req=server.AgentRuntimeInvokeRequest(
            payload={"type": "room.workspace.runtime.invoke"},
            timeout_seconds=21.0,
        ),
    )

    assert response["env"] == "env-runtime"
    assert response["service_id"] == "codex"
    assert response["runtime_id"] == "codex"
    assert response["runtime_profile"] == "codex_app_server"
    assert response["status"] == "completed"
    assert response["response"] == {
        "success": True,
        "output_text": "Codex websocket reply.",
    }


@pytest.mark.asyncio
async def test_invoke_agent_runtime_uses_command_path(monkeypatch: pytest.MonkeyPatch) -> None:
    declared = _declared_runtime_service(runtime_profile="codex_exec")
    discovered = _discovered_runtime_service(runtime_profile="codex_exec")

    monkeypatch.setattr(
        server,
        "lxc",
        lambda *args: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(server, "_read_service_manifest", lambda name: [declared])
    monkeypatch.setattr(server, "_discover_service", lambda name, service: discovered)

    def fake_invoke_agent_runtime_command(
        *,
        env_name,
        service,
        argv,
        cwd,
        user,
        timeout_seconds,
    ):
        assert env_name == "env-runtime"
        assert service == declared
        assert argv == ["codex", "exec", "Inspect the repository."]
        assert cwd == "/workspace"
        assert user == "dev"
        assert timeout_seconds == 30.0
        return {
            "status": "completed",
            "transport_kind": "command",
            "protocol": "process",
            "response": {"success": True, "output_text": "Codex exec reply."},
        }

    async def fake_to_thread(fn, /, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(
        server,
        "_invoke_agent_runtime_command",
        fake_invoke_agent_runtime_command,
    )
    monkeypatch.setattr(server.asyncio, "to_thread", fake_to_thread)

    response = await server.invoke_agent_runtime(
        name="env-runtime",
        service_id="codex",
        req=server.AgentRuntimeInvokeRequest(
            invoke_mode="command",
            argv=["codex", "exec", "Inspect the repository."],
            cwd="/workspace",
            user="dev",
            timeout_seconds=30.0,
        ),
    )

    assert response["env"] == "env-runtime"
    assert response["service_id"] == "codex"
    assert response["runtime_id"] == "codex"
    assert response["runtime_profile"] == "codex_exec"
    assert response["status"] == "completed"
    assert response["response"] == {
        "success": True,
        "output_text": "Codex exec reply.",
    }


@pytest.mark.asyncio
async def test_invoke_agent_runtime_uses_json_rpc_path(monkeypatch: pytest.MonkeyPatch) -> None:
    declared = _declared_runtime_service()
    discovered = _discovered_runtime_service()

    monkeypatch.setattr(
        server,
        "lxc",
        lambda *args: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(server, "_read_service_manifest", lambda name: [declared])
    monkeypatch.setattr(server, "_discover_service", lambda name, service: discovered)

    async def fake_invoke_agent_runtime_json_rpc(*, service, session_request, timeout_seconds):
        assert service == discovered
        assert timeout_seconds == 18.0
        assert [request.method for request in session_request.requests] == [
            "initialize",
            "thread/start",
        ]
        assert session_request.terminal_notification_methods == ["turn/completed"]
        return {
            "status": "completed",
            "transport_kind": "websocket",
            "protocol": "ws",
            "response": {
                "responses": [{"id": "initialize", "result": {"platformOs": "linux"}}],
                "notifications": [],
                "terminal_notification": {"method": "turn/completed", "params": {}},
            },
        }

    monkeypatch.setattr(
        server,
        "_invoke_agent_runtime_json_rpc",
        fake_invoke_agent_runtime_json_rpc,
    )

    response = await server.invoke_agent_runtime(
        name="env-runtime",
        service_id="codex",
        req=server.AgentRuntimeInvokeRequest(
            invoke_mode="json_rpc",
            json_rpc_session=server.JsonRpcInvokeSessionRequest(
                requests=[
                    server.JsonRpcInvokeRequestMessage(
                        id="initialize",
                        method="initialize",
                        params={"clientInfo": {"name": "dog", "version": "1"}},
                    ),
                    server.JsonRpcInvokeRequestMessage(
                        id="thread/start",
                        method="thread/start",
                        params={"cwd": "/workspace"},
                    ),
                ],
                terminal_notification_methods=["turn/completed"],
            ),
            timeout_seconds=18.0,
        ),
    )

    assert response["env"] == "env-runtime"
    assert response["service_id"] == "codex"
    assert response["runtime_id"] == "codex"
    assert response["runtime_profile"] == "codex_app_server"
    assert response["status"] == "completed"
    assert response["response"]["terminal_notification"]["method"] == "turn/completed"


@pytest.mark.asyncio
async def test_invoke_agent_runtime_uses_http_path(monkeypatch: pytest.MonkeyPatch) -> None:
    declared = _declared_runtime_service(
        service_id="hermes_api",
        runtime_id="hermes",
        runtime_profile="hermes_api_server",
        transport_kind="http",
        protocol="http",
    )
    discovered = _discovered_runtime_service(
        service_id="hermes_api",
        runtime_id="hermes",
        runtime_profile="hermes_api_server",
        transport_kind="http",
        protocol="http",
    )

    monkeypatch.setattr(
        server,
        "lxc",
        lambda *args: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(server, "_read_service_manifest", lambda name: [declared])
    monkeypatch.setattr(server, "_discover_service", lambda name, service: discovered)

    def fake_invoke_agent_runtime_http(
        *,
        env_name,
        service,
        payload,
        path,
        timeout_seconds,
    ):
        assert env_name == "env-runtime"
        assert service == declared
        assert payload["model"] == "hermes"
        assert path == "/v1/chat/completions"
        assert timeout_seconds == 30.0
        return {
            "status": "completed",
            "transport_kind": "http",
            "protocol": "http",
            "response": {
                "choices": [
                    {"message": {"content": "Hermes HTTP reply."}},
                ],
            },
        }

    async def fake_to_thread(fn, /, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(
        server,
        "_invoke_agent_runtime_http",
        fake_invoke_agent_runtime_http,
    )
    monkeypatch.setattr(server.asyncio, "to_thread", fake_to_thread)

    response = await server.invoke_agent_runtime(
        name="env-runtime",
        service_id="hermes_api",
        req=server.AgentRuntimeInvokeRequest(
            invoke_mode="http",
            payload={"model": "hermes", "messages": []},
            http_path="/v1/chat/completions",
            timeout_seconds=30.0,
        ),
    )

    assert response["env"] == "env-runtime"
    assert response["service_id"] == "hermes_api"
    assert response["runtime_id"] == "hermes"
    assert response["runtime_profile"] == "hermes_api_server"
    assert response["status"] == "completed"
    assert response["response"]["choices"][0]["message"]["content"] == "Hermes HTTP reply."


@pytest.mark.asyncio
async def test_invoke_agent_runtime_rejects_unsupported_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    declared = _declared_runtime_service(
        service_id="custom_runtime",
        runtime_id="custom_runtime",
        runtime_profile=None,
        transport_kind="http",
    )
    discovered = _discovered_runtime_service(
        service_id="custom_runtime",
        runtime_id="custom_runtime",
        runtime_profile=None,
        transport_kind="http",
    )

    monkeypatch.setattr(
        server,
        "lxc",
        lambda *args: SimpleNamespace(returncode=0),
    )
    monkeypatch.setattr(server, "_read_service_manifest", lambda name: [declared])
    monkeypatch.setattr(server, "_discover_service", lambda name, service: discovered)

    with pytest.raises(HTTPException) as exc_info:
        await server.invoke_agent_runtime(
            name="env-runtime",
            service_id="custom_runtime",
            req=server.AgentRuntimeInvokeRequest(
                payload={"type": "room.workspace.runtime.invoke"},
            ),
        )

    assert exc_info.value.status_code == 400
    assert "not supported by the kennel invoke endpoint yet" in str(exc_info.value.detail)
