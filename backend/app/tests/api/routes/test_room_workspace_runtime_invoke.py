from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.room_workspace_connection_service import RoomWorkspaceRuntimeTarget
from app.services.room_workspace_runtime_execution_service import (
    RoomWorkspaceRuntimeConnectionError,
    RoomWorkspaceRuntimeInvocationResult,
)
from app.services.room_workspace_runtime_orchestrator import (
    RoomWorkspaceRuntimeInvocationExecution,
)


def test_invoke_room_workspace_runtime_emits_room_agent_message(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    api_test_room,
) -> None:
    target = RoomWorkspaceRuntimeTarget(
        connection_id=str(uuid4()),
        room_id=api_test_room.room_id,
        workspace_id=uuid4(),
        workspace_name="Runtime Workspace",
        kennel_name="env-runtime",
        workspace_path="/home/dev/workspace",
        descriptor_id=str(uuid4()),
        endpoint_id="codex",
        endpoint_label="Codex Runtime",
        runtime_id="codex",
        runtime_profile="codex_app_server",
        transport_kind="websocket",
        protocol="ws",
        url="ws://runtime.internal/socket",
        scope={
            "room_id": str(api_test_room.room_id),
            "workspace_id": str(uuid4()),
            "purpose": "agent_runtime_connect",
            "endpoint_id": "codex",
        },
    )
    invocation_result = RoomWorkspaceRuntimeInvocationResult(
        request_id="runtime-request-1",
        connection_id=target.connection_id,
        workspace_id=str(target.workspace_id),
        endpoint_id=target.endpoint_id,
        runtime_label=target.endpoint_label,
        protocol=target.protocol,
        success=True,
        output_text="Runtime completed the requested work.",
        raw={"output_text": "Runtime completed the requested work."},
    )

    with (
        patch(
            "app.api.routes.rooms.invoke_room_workspace_runtime_orchestrated",
            new=AsyncMock(
                return_value=RoomWorkspaceRuntimeInvocationExecution(
                    target=target,
                    result=invocation_result,
                    invocation=type("_Invocation", (), {"id": uuid4()})(),
                )
            ),
        ) as mock_invoke,
    ):
        response = client.post(
            f"{settings.API_V1_STR}/rooms/{api_test_room.room_id}/workspace-runtime/invoke",
            headers=superuser_token_headers,
            json={"input": "Please inspect the repository."},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["request_id"] == "runtime-request-1"
    assert data["invocation_id"] is not None
    assert data["connection_id"] == target.connection_id
    assert data["endpoint_id"] == "codex"
    assert data["runtime_label"] == "Codex Runtime"
    assert data["runtime_id"] == "codex"
    assert data["runtime_profile"] == "codex_app_server"
    assert data["success"] is True
    assert data["output_text"] == "Runtime completed the requested work."
    assert data["message_id"] is not None

    mock_invoke.assert_awaited_once()

    messages_response = client.get(
        f"{settings.API_V1_STR}/rooms/{api_test_room.room_id}/messages",
        headers=superuser_token_headers,
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()["data"]
    runtime_messages = [
        message for message in messages if message["agent_name"] == "Codex Runtime"
    ]
    assert runtime_messages
    assert runtime_messages[0]["content"] == "Runtime completed the requested work."


def test_invoke_room_workspace_runtime_returns_structured_error_detail(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    api_test_room,
) -> None:
    with patch(
        "app.api.routes.rooms.invoke_room_workspace_runtime_orchestrated",
        new=AsyncMock(
            side_effect=RoomWorkspaceRuntimeConnectionError(
                "Runtime invocation failed while opening the websocket connection.",
            )
        ),
    ):
        response = client.post(
            f"{settings.API_V1_STR}/rooms/{api_test_room.room_id}/workspace-runtime/invoke",
            headers=superuser_token_headers,
            json={"input": "Please inspect the repository."},
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "failed",
            "error_category": "connection_error",
            "error_phase": "connect",
            "message": "Runtime invocation failed while opening the websocket connection.",
        }
    }
