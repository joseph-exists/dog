from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest
from sqlmodel import select

from app.models import (
    RoomWorkspaceRuntimeInvocation,
    RoomWorkspaceRuntimeInvocationStatus,
)
from app.services.room_workspace_connection_service import RoomWorkspaceRuntimeTarget
from app.services.room_workspace_runtime_execution_service import (
    RoomWorkspaceRuntimeExecutionError,
    RoomWorkspaceRuntimeInvocationCaller,
    RoomWorkspaceRuntimeInvocationRequest,
    RoomWorkspaceRuntimeInvocationResult,
)
from app.services.room_workspace_runtime_orchestrator import (
    CodexRoomWorkspaceRuntimeAdapter,
    get_room_workspace_runtime_adapter_registry,
    KennelRoutedRoomWorkspaceRuntimeAdapter,
    RoomWorkspaceRuntimeAdapterRegistry,
    invoke_room_workspace_runtime,
)


def _runtime_target(*, runtime_id: str = "codex") -> RoomWorkspaceRuntimeTarget:
    return RoomWorkspaceRuntimeTarget(
        connection_id=str(uuid4()),
        room_id=uuid4(),
        workspace_id=uuid4(),
        workspace_name="Runtime Workspace",
        kennel_name="env-runtime",
        workspace_path="/home/dev/workspace",
        descriptor_id=str(uuid4()),
        endpoint_id=runtime_id,
        endpoint_label="Runtime",
        runtime_id=runtime_id,
        runtime_profile="codex_app_server" if runtime_id == "codex" else None,
        transport_kind="websocket",
        protocol="ws",
        url="ws://runtime.internal/socket",
        scope={"purpose": "agent_runtime_connect"},
    )


@dataclass
class _FakeAdapter:
    result: RoomWorkspaceRuntimeInvocationResult
    called: bool = False

    async def invoke(self, request):
        self.called = True
        assert request.target.runtime_id == "codex"
        assert request.input == "Inspect the repository."
        assert request.caller.kind == "user"
        return self.result


@pytest.mark.asyncio
async def test_runtime_orchestrator_uses_registered_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _runtime_target(runtime_id="codex")
    result = RoomWorkspaceRuntimeInvocationResult(
        request_id="runtime-request-1",
        connection_id=target.connection_id,
        workspace_id=str(target.workspace_id),
        endpoint_id=target.endpoint_id,
        runtime_label=target.endpoint_label,
        protocol=target.protocol,
        success=True,
        output_text="Codex completed the request.",
        raw={"output_text": "Codex completed the request."},
    )
    adapter = _FakeAdapter(result=result)
    registry = RoomWorkspaceRuntimeAdapterRegistry(
        adapters_by_runtime_id={"codex": adapter},
        default_adapter=None,
    )

    async def fake_consume_current_room_workspace_runtime_target(session, *, room_id, context_store=None):  # noqa: ARG001
        return target

    monkeypatch.setattr(
        "app.services.room_workspace_runtime_orchestrator.consume_current_room_workspace_runtime_target",
        fake_consume_current_room_workspace_runtime_target,
    )

    execution = await invoke_room_workspace_runtime(
        session=None,  # type: ignore[arg-type]
        room_id=target.room_id,
        input="Inspect the repository.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id=str(uuid4())),
        adapter_registry=registry,
    )

    assert adapter.called is True
    assert execution.target == target
    assert execution.result == result
    assert execution.invocation.status == RoomWorkspaceRuntimeInvocationStatus.completed


def test_runtime_adapter_registry_rejects_unknown_runtime_without_default() -> None:
    registry = RoomWorkspaceRuntimeAdapterRegistry(
        adapters_by_runtime_id={},
        default_adapter=None,
    )

    with pytest.raises(RoomWorkspaceRuntimeExecutionError) as exc_info:
        registry.resolve(_runtime_target(runtime_id="unknown"))

    assert "No runtime adapter is registered" in str(exc_info.value)


def test_default_runtime_adapter_registry_resolves_current_runtime_ids() -> None:
    registry = get_room_workspace_runtime_adapter_registry()

    codex_adapter = registry.resolve(_runtime_target(runtime_id="codex"))
    claude_adapter = registry.resolve(_runtime_target(runtime_id="claude_code"))
    hermes_adapter = registry.resolve(_runtime_target(runtime_id="hermes"))

    assert isinstance(codex_adapter, CodexRoomWorkspaceRuntimeAdapter)
    assert isinstance(claude_adapter, KennelRoutedRoomWorkspaceRuntimeAdapter)
    assert isinstance(hermes_adapter, KennelRoutedRoomWorkspaceRuntimeAdapter)


@pytest.mark.asyncio
async def test_kennel_routed_adapter_invokes_kennel_runtime_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _runtime_target(runtime_id="codex")
    request_id = "runtime-request-2"
    adapter = KennelRoutedRoomWorkspaceRuntimeAdapter(timeout_seconds=22.0)

    async def fake_invoke_agent_runtime(kennel_name, *, service_id, payload, timeout_seconds=15.0):  # noqa: ARG001
        assert kennel_name == "env-runtime"
        assert service_id == "codex"
        assert timeout_seconds == 22.0
        assert payload["type"] == "room.workspace.runtime.invoke"
        assert payload["room_context"]["workspace_id"] == str(target.workspace_id)
        return {
            "status": "completed",
            "response": {
                "request_id": request_id,
                "success": True,
                "output_text": "Codex completed through kennel.",
            },
        }

    monkeypatch.setattr(
        "app.services.room_workspace_runtime_orchestrator.kennel_client.invoke_agent_runtime",
        fake_invoke_agent_runtime,
    )

    result = await adapter.invoke(
        RoomWorkspaceRuntimeInvocationRequest(
            target=target,
            input="Inspect the repository.",
            caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id=str(uuid4())),
            request_id=request_id,
        )
    )

    assert result.request_id == request_id
    assert result.success is True
    assert result.output_text == "Codex completed through kennel."


@pytest.mark.asyncio
async def test_codex_adapter_uses_websocket_path_for_codex_app_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _runtime_target(runtime_id="codex")
    adapter = CodexRoomWorkspaceRuntimeAdapter()
    request = RoomWorkspaceRuntimeInvocationRequest(
        target=target,
        input="Inspect the repository.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id=str(uuid4())),
    )

    calls: list[dict[str, object]] = []

    async def fake_invoke_agent_runtime(kennel_name, *, service_id, payload=None, json_rpc_session=None, invoke_mode="websocket", argv=None, cwd=None, user=None, timeout_seconds=15.0):  # noqa: ARG001
        assert kennel_name == "env-runtime"
        assert service_id == "codex"
        assert invoke_mode == "json_rpc"
        assert payload is None
        assert isinstance(json_rpc_session, dict)
        calls.append(json_rpc_session)
        request_methods = [
            frame["method"]
            for frame in json_rpc_session.get("requests", [])
            if isinstance(frame, dict)
        ]
        if request_methods == ["initialize", "thread/start"]:
            return {
                "status": "completed",
                "response": {
                    "responses": [
                        {"id": "initialize", "result": {"platformOs": "linux"}},
                        {
                            "id": "thread/start",
                            "result": {
                                "thread": {
                                    "id": "thread-1",
                                }
                            },
                        },
                    ],
                    "notifications": [],
                    "terminal_notification": None,
                },
            }
        if request_methods == ["initialize", "turn/start"]:
            return {
                "status": "completed",
                "response": {
                    "responses": [
                        {"id": "initialize", "result": {"platformOs": "linux"}},
                        {
                            "id": "turn/start",
                            "result": {
                                "turn": {
                                    "id": "turn-1",
                                }
                            },
                        },
                    ],
                    "notifications": [
                        {
                            "method": "item/agentMessage/delta",
                            "params": {"delta": "Codex app server "},
                        },
                        {
                            "method": "item/agentMessage/delta",
                            "params": {"delta": "completed the request."},
                        },
                        {
                            "method": "turn/completed",
                            "params": {"threadId": "thread-1", "turn": {"id": "turn-1"}},
                        },
                    ],
                    "terminal_notification": {
                        "method": "turn/completed",
                        "params": {"threadId": "thread-1", "turn": {"id": "turn-1"}},
                    },
                },
            }
        raise AssertionError(f"Unexpected JSON-RPC request methods: {request_methods}")

    monkeypatch.setattr(
        "app.services.room_workspace_runtime_orchestrator.kennel_client.invoke_agent_runtime",
        fake_invoke_agent_runtime,
    )

    result = await adapter.invoke(request)

    assert len(calls) == 2
    assert result.success is True
    assert result.output_text == "Codex app server completed the request."


@pytest.mark.asyncio
async def test_codex_adapter_uses_command_mode_for_codex_exec_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _runtime_target(runtime_id="codex")
    target = RoomWorkspaceRuntimeTarget(
        **{
            **target.__dict__,
            "runtime_profile": "codex_exec",
        }
    )
    adapter = CodexRoomWorkspaceRuntimeAdapter()
    request = RoomWorkspaceRuntimeInvocationRequest(
        target=target,
        input="Summarize the repository.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id=str(uuid4())),
    )

    async def fake_invoke_agent_runtime(kennel_name, *, service_id, payload=None, invoke_mode="websocket", argv=None, cwd=None, user=None, timeout_seconds=15.0):  # noqa: ARG001
        assert kennel_name == "env-runtime"
        assert service_id == "codex"
        assert payload is None
        assert invoke_mode == "command"
        assert argv == ["codex", "exec", "Summarize the repository."]
        assert cwd == "/home/dev/workspace"
        assert user == "dev"
        return {
            "status": "completed",
            "response": {
                "request_id": request.request_id,
                "success": True,
                "output_text": "Codex exec completed the request.",
            },
        }

    monkeypatch.setattr(
        "app.services.room_workspace_runtime_orchestrator.kennel_client.invoke_agent_runtime",
        fake_invoke_agent_runtime,
    )

    result = await adapter.invoke(request)

    assert result.success is True
    assert result.output_text == "Codex exec completed the request."


@pytest.mark.asyncio
async def test_runtime_orchestrator_persists_invocation_record_lifecycle(
    async_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _runtime_target(runtime_id="codex")
    result = RoomWorkspaceRuntimeInvocationResult(
        request_id="runtime-request-persisted",
        connection_id=target.connection_id,
        workspace_id=str(target.workspace_id),
        endpoint_id=target.endpoint_id,
        runtime_label=target.endpoint_label,
        protocol=target.protocol,
        success=True,
        output_text="Persisted runtime output.",
        raw={"output_text": "Persisted runtime output."},
    )
    adapter = _FakeAdapter(result=result)
    registry = RoomWorkspaceRuntimeAdapterRegistry(
        adapters_by_runtime_id={"codex": adapter},
        default_adapter=None,
    )

    async def fake_consume_current_room_workspace_runtime_target(session, *, room_id, context_store=None):  # noqa: ARG001
        return target

    monkeypatch.setattr(
        "app.services.room_workspace_runtime_orchestrator.consume_current_room_workspace_runtime_target",
        fake_consume_current_room_workspace_runtime_target,
    )

    execution = await invoke_room_workspace_runtime(
        session=async_session,
        room_id=target.room_id,
        input="Inspect the repository.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id="user-1"),
        adapter_registry=registry,
    )

    statement = select(RoomWorkspaceRuntimeInvocation).where(
        RoomWorkspaceRuntimeInvocation.id == execution.invocation.id
    )
    persisted = (await async_session.exec(statement)).first()

    assert persisted is not None
    assert persisted.request_id == execution.result.request_id
    assert persisted.room_id == target.room_id
    assert persisted.workspace_id == target.workspace_id
    assert persisted.connection_id == target.connection_id
    assert persisted.runtime_id == "codex"
    assert persisted.runtime_profile == "codex_app_server"
    assert persisted.caller_kind == "user"
    assert persisted.caller_id == "user-1"
    assert persisted.status == RoomWorkspaceRuntimeInvocationStatus.completed
    assert persisted.error_category is None
    assert persisted.completed_at is not None
