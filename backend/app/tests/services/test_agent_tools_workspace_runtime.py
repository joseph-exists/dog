from __future__ import annotations

import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.agent_tools import AgentDeps, invoke_connected_workspace_runtime
from app.services.room_workspace_connection_service import RoomWorkspaceRuntimeTarget
from app.services.room_workspace_runtime_execution_service import (
    RoomWorkspaceRuntimeInvocationResult,
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
        descriptor_id=str(uuid4()),
        endpoint_id="runtime",
        endpoint_label="Hermes Runtime",
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

    async def fake_consume_current_room_workspace_runtime_target(session, *, room_id, context_store=None):  # noqa: ARG001
        return target

    async def fake_execute_room_workspace_runtime_invocation(request, *, timeout_seconds=15.0, websocket_connect=None):  # noqa: ARG001
        assert request.input == "Inspect the room state."
        assert request.caller.kind == "agent"
        assert request.caller.id == "story-advisor"
        return invocation_result

    monkeypatch.setattr(
        "app.services.agent_tools.consume_current_room_workspace_runtime_target",
        fake_consume_current_room_workspace_runtime_target,
    )
    monkeypatch.setattr(
        "app.services.agent_tools.execute_room_workspace_runtime_invocation",
        fake_execute_room_workspace_runtime_invocation,
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
