from __future__ import annotations

import asyncio
import json
from uuid import uuid4

import pytest

from app.services.room_workspace_connection_service import RoomWorkspaceRuntimeTarget
from app.services.room_workspace_runtime_execution_service import (
    RoomWorkspaceRuntimeConnectionError,
    RoomWorkspaceRuntimeExecutionError,
    RoomWorkspaceRuntimeInvocationCaller,
    RoomWorkspaceRuntimeInvocationRequest,
    RoomWorkspaceRuntimeResponseTimeoutError,
    build_room_workspace_runtime_invocation_message,
    execute_room_workspace_runtime_invocation,
)


def _runtime_target(*, protocol: str = "ws") -> RoomWorkspaceRuntimeTarget:
    return RoomWorkspaceRuntimeTarget(
        connection_id=str(uuid4()),
        room_id=uuid4(),
        workspace_id=uuid4(),
        workspace_name="Runtime Workspace",
        descriptor_id=str(uuid4()),
        endpoint_id="runtime",
        endpoint_label="Generic Runtime",
        protocol=protocol,
        url="ws://runtime.internal/socket",
        scope={
            "room_id": str(uuid4()),
            "workspace_id": str(uuid4()),
            "purpose": "agent_runtime_connect",
            "endpoint_id": "runtime",
        },
    )


class _FakeWebSocket:
    def __init__(self, response):
        self.response = response
        self.sent_messages: list[str] = []

    async def send(self, message: str) -> None:
        self.sent_messages.append(message)

    async def recv(self):
        return self.response


class _FakeConnection:
    def __init__(self, websocket: _FakeWebSocket):
        self.websocket = websocket
        self.exited = False

    async def __aenter__(self) -> _FakeWebSocket:
        return self.websocket

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.exited = True
        return None


def _fake_connect_factory(websocket: _FakeWebSocket):
    def _connect(url: str, *, open_timeout: float, close_timeout: float):
        assert url == "ws://runtime.internal/socket"
        assert open_timeout > 0
        assert close_timeout > 0
        return _FakeConnection(websocket)

    return _connect


def test_build_runtime_invocation_message_uses_shared_envelope() -> None:
    request = RoomWorkspaceRuntimeInvocationRequest(
        target=_runtime_target(),
        input="Inspect the current workspace state.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id=str(uuid4())),
    )

    message = build_room_workspace_runtime_invocation_message(request)

    assert message["type"] == "room.workspace.runtime.invoke"
    assert message["request_id"] == request.request_id
    assert message["caller"]["kind"] == "user"
    assert message["input"] == "Inspect the current workspace state."
    assert message["room_context"]["connection_id"] == request.target.connection_id
    assert message["room_context"]["endpoint_id"] == request.target.endpoint_id


@pytest.mark.asyncio
async def test_execute_runtime_invocation_sends_shared_message_and_normalizes_json_response() -> None:
    websocket = _FakeWebSocket(
        json.dumps(
            {
                "request_id": "runtime-req-1",
                "success": True,
                "output_text": "Runtime completed successfully.",
                "runtime": "claude_code",
            }
        )
    )
    request = RoomWorkspaceRuntimeInvocationRequest(
        target=_runtime_target(),
        input="Please summarize the repository structure.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="agent", id="story-advisor"),
    )

    result = await execute_room_workspace_runtime_invocation(
        request,
        websocket_connect=_fake_connect_factory(websocket),
    )

    assert len(websocket.sent_messages) == 1
    sent_message = json.loads(websocket.sent_messages[0])
    assert sent_message["type"] == "room.workspace.runtime.invoke"
    assert sent_message["input"] == "Please summarize the repository structure."
    assert sent_message["caller"]["kind"] == "agent"
    assert sent_message["caller"]["id"] == "story-advisor"

    assert result.request_id == "runtime-req-1"
    assert result.success is True
    assert result.output_text == "Runtime completed successfully."
    assert result.raw["runtime"] == "claude_code"


@pytest.mark.asyncio
async def test_execute_runtime_invocation_normalizes_plain_text_response() -> None:
    websocket = _FakeWebSocket("Hermes has completed the requested analysis.")
    request = RoomWorkspaceRuntimeInvocationRequest(
        target=_runtime_target(),
        input="Analyze the active room context.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id=str(uuid4())),
    )

    result = await execute_room_workspace_runtime_invocation(
        request,
        websocket_connect=_fake_connect_factory(websocket),
    )

    assert result.success is True
    assert result.output_text == "Hermes has completed the requested analysis."
    assert result.raw == "Hermes has completed the requested analysis."


@pytest.mark.asyncio
async def test_execute_runtime_invocation_rejects_non_websocket_protocol() -> None:
    request = RoomWorkspaceRuntimeInvocationRequest(
        target=_runtime_target(protocol="http"),
        input="This should not execute.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id=str(uuid4())),
    )

    with pytest.raises(RoomWorkspaceRuntimeExecutionError) as exc_info:
        await execute_room_workspace_runtime_invocation(request)

    assert "not supported by the websocket execution adapter" in str(exc_info.value)


def _timeout_connect(*args, **kwargs):
    raise asyncio.TimeoutError()


@pytest.mark.asyncio
async def test_execute_runtime_invocation_reports_websocket_open_timeout() -> None:
    request = RoomWorkspaceRuntimeInvocationRequest(
        target=_runtime_target(),
        input="This connection should time out before opening.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id=str(uuid4())),
    )

    with pytest.raises(RoomWorkspaceRuntimeConnectionError) as exc_info:
        await execute_room_workspace_runtime_invocation(
            request,
            websocket_connect=_timeout_connect,
        )

    assert "failed while opening the websocket connection" in str(exc_info.value)


class _RecvTimeoutWebSocket(_FakeWebSocket):
    async def recv(self):
        raise asyncio.TimeoutError()


@pytest.mark.asyncio
async def test_execute_runtime_invocation_reports_response_timeout_after_open() -> None:
    websocket = _RecvTimeoutWebSocket(response=None)
    request = RoomWorkspaceRuntimeInvocationRequest(
        target=_runtime_target(),
        input="This runtime should not respond.",
        caller=RoomWorkspaceRuntimeInvocationCaller(kind="user", id=str(uuid4())),
    )

    with pytest.raises(RoomWorkspaceRuntimeResponseTimeoutError) as exc_info:
        await execute_room_workspace_runtime_invocation(
            request,
            websocket_connect=_fake_connect_factory(websocket),
        )

    assert "while waiting for a response" in str(exc_info.value)
