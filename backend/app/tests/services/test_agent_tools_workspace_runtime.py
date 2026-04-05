from __future__ import annotations

import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.agent_tools import AgentDeps, invoke_connected_workspace_runtime
from app.services.room_workspace_connection_service import RoomWorkspaceRuntimeTarget
from app.services.room_workspace_runtime_execution_service import (
    RoomWorkspaceRuntimeInvocationCaller,
    RoomWorkspaceRuntimeInvocationResult,
)
from app.services.room_workspace_runtime_orchestrator import (
    RoomWorkspaceRuntimeInvocationExecution,
)


@pytest.mark.asyncio
async def test_invoke_connected_workspace_runtime_returns_normalized_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = RoomWorkspaceRuntimeTarget(
        connection_id=str(uuid4()),
        room_id=uuid4(),
        workspace_id=uuid4(),
        workspace_name="Runtime Workspace",
        kennel_name="env-runtime",
        workspace_path="/home/dev/workspace",
        descriptor_id=str(uuid4()),
        endpoint_id="runtime",
        endpoint_label="Hermes Runtime",
        runtime_id="hermes",
        runtime_profile=None,
        transport_kind="websocket",
        protocol="ws",
        url="ws://runtime.internal/socket",
        scope={"purpose": "agent_runtime_connect"},
    )
    invocation_result = RoomWorkspaceRuntimeInvocationResult(
        request_id="runtime-request-1",
        connection_id=target.connection_id,
        workspace_id=str(target.workspace_id),
        endpoint_id=target.endpoint_id,
        runtime_label=target.endpoint_label,
        protocol=target.protocol,
        success=True,
        output_text="Hermes completed the task.",
        raw={"output_text": "Hermes completed the task."},
    )

    async def fake_invoke_room_workspace_runtime(session, *, room_id, input, caller, adapter_registry=None):  # noqa: ARG001,A002
        assert input == "Inspect the room state."
        assert isinstance(caller, RoomWorkspaceRuntimeInvocationCaller)
        assert caller.kind == "agent"
        assert caller.id == "story-advisor"
        return RoomWorkspaceRuntimeInvocationExecution(
            target=target,
            result=invocation_result,
            invocation=type("_Invocation", (), {"id": uuid4()})(),
        )

    monkeypatch.setattr(
        "app.services.agent_tools.invoke_room_workspace_runtime",
        fake_invoke_room_workspace_runtime,
    )

    ctx = SimpleNamespace(
        deps=AgentDeps(
            session=None,  # type: ignore[arg-type]
            room_id=uuid4(),
            current_agent_slug="story-advisor",
        )
    )

    result = await invoke_connected_workspace_runtime(
        ctx,
        "Inspect the room state.",
    )

    payload = json.loads(result)
    assert payload["request_id"] == "runtime-request-1"
    assert payload["runtime_label"] == "Hermes Runtime"
    assert payload["success"] is True
    assert payload["output_text"] == "Hermes completed the task."
    assert payload["invocation_id"] is not None
