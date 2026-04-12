from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models import (
    RoomWorkspaceConnectionPurpose,
    Workspace,
    WorkspaceServiceKind,
    WorkspaceServiceProtocol,
    WorkspaceServiceSource,
    WorkspaceServiceStatus,
    WorkspaceServiceSummary,
    WorkspaceStatus,
)
from app.services.context_store import ContextItem, InMemoryContextStore
from app.services.room_workspace_connection_service import (
    CURRENT_CONNECTION_CONTEXT_TYPE,
    RoomWorkspaceRuntimeTargetResolutionError,
    consume_current_room_workspace_runtime_target,
)


def _current_connection_payload(
    *,
    workspace_id: str,
    workspace_name: str,
    purpose: str = "agent_runtime_connect",
    selected_at: datetime | None = None,
) -> dict[str, object]:
    return {
        "connection_id": str(uuid4()),
        "workspace_id": workspace_id,
        "workspace_name": workspace_name,
        "purpose": purpose,
        "relationship": "owner_private",
        "access_level": "use",
        "service_count": 1,
        "ready_service_count": 1,
        "selected_at": (selected_at or datetime.now(timezone.utc)).isoformat(),
    }


@pytest.mark.asyncio
async def test_consume_runtime_target_returns_active_runtime_endpoint(
    async_session,
    test_room,
    test_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = Workspace(
        id=uuid4(),
        owner_id=test_user.id,
        name="Runtime Workspace",
        status=WorkspaceStatus.ready,
        kennel_name="env-runtime",
        meta={"bootstrap_workspace_path": "/home/dev/workspace"},
    )
    async_session.add(workspace)
    await async_session.commit()

    async def _mock_get_workspace_service_summaries(_workspace: Workspace):
        return [
            WorkspaceServiceSummary(
                id="codex",
                kind=WorkspaceServiceKind.agent_runtime,
                label="Codex Runtime",
                runtime_id="codex",
                runtime_profile="codex_app_server",
                transport_kind="websocket",
                status=WorkspaceServiceStatus.ready,
                protocol=WorkspaceServiceProtocol.ws,
                url="ws://runtime.internal:4500",
                source=WorkspaceServiceSource.runtime_probe,
            )
        ]

    monkeypatch.setattr(
        "app.services.room_workspace_connection_service.get_workspace_service_summaries",
        _mock_get_workspace_service_summaries,
    )

    store = InMemoryContextStore()
    await store.add(
        ContextItem(
            id="runtime-connection",
            room_id=test_room.room_id,
            agent_slug=None,
            context_type=CURRENT_CONNECTION_CONTEXT_TYPE,
            payload=_current_connection_payload(
                workspace_id=str(workspace.id),
                workspace_name=workspace.name,
            ),
            source="system",
            created_at=datetime.now(timezone.utc),
        )
    )

    target = await consume_current_room_workspace_runtime_target(
        async_session,
        room_id=test_room.room_id,
        context_store=store,
    )

    assert target.room_id == test_room.room_id
    assert target.workspace_id == workspace.id
    assert target.kennel_name == "env-runtime"
    assert target.workspace_path == "/home/dev/workspace"
    assert target.endpoint_id == "codex"
    assert target.endpoint_label == "Codex Runtime"
    assert target.runtime_id == "codex"
    assert target.runtime_profile == "codex_app_server"
    assert target.transport_kind == "websocket"
    assert target.protocol == "ws"
    assert target.url == "ws://runtime.internal:4500"
    assert target.scope["purpose"] == RoomWorkspaceConnectionPurpose.agent_runtime_connect.value


@pytest.mark.asyncio
async def test_consume_runtime_target_accepts_http_agent_runtime_endpoint(
    async_session,
    test_room,
    test_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = Workspace(
        id=uuid4(),
        owner_id=test_user.id,
        name="Hermes API Workspace",
        status=WorkspaceStatus.ready,
        kennel_name="env-hermes-api",
        meta={"bootstrap_workspace_path": "/home/dev/workspace"},
    )
    async_session.add(workspace)
    await async_session.commit()

    async def _mock_get_workspace_service_summaries(_workspace: Workspace):
        return [
            WorkspaceServiceSummary(
                id="hermes_api",
                kind=WorkspaceServiceKind.agent_runtime,
                label="Hermes API Server",
                runtime_id="hermes",
                runtime_profile="hermes_api_server",
                transport_kind="http",
                status=WorkspaceServiceStatus.ready,
                protocol=WorkspaceServiceProtocol.http,
                url="http://runtime.internal:8642/",
                source=WorkspaceServiceSource.runtime_probe,
            )
        ]

    monkeypatch.setattr(
        "app.services.room_workspace_connection_service.get_workspace_service_summaries",
        _mock_get_workspace_service_summaries,
    )

    store = InMemoryContextStore()
    await store.add(
        ContextItem(
            id="runtime-connection-http",
            room_id=test_room.room_id,
            agent_slug=None,
            context_type=CURRENT_CONNECTION_CONTEXT_TYPE,
            payload=_current_connection_payload(
                workspace_id=str(workspace.id),
                workspace_name=workspace.name,
            ),
            source="system",
            created_at=datetime.now(timezone.utc),
        )
    )

    target = await consume_current_room_workspace_runtime_target(
        async_session,
        room_id=test_room.room_id,
        context_store=store,
    )

    assert target.runtime_id == "hermes"
    assert target.runtime_profile == "hermes_api_server"
    assert target.transport_kind == "http"
    assert target.protocol == "http"
    assert target.url == "http://runtime.internal:8642/"


@pytest.mark.asyncio
async def test_consume_runtime_target_rejects_non_runtime_current_connection(
    async_session,
    test_room,
    test_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = Workspace(
        id=uuid4(),
        owner_id=test_user.id,
        name="Service Workspace",
        status=WorkspaceStatus.ready,
        kennel_name="env-service",
    )
    async_session.add(workspace)
    await async_session.commit()

    async def _mock_get_workspace_service_summaries(_workspace: Workspace):
        return [
            WorkspaceServiceSummary(
                id="web",
                kind=WorkspaceServiceKind.web_app,
                label="Frontend",
                status=WorkspaceServiceStatus.ready,
                protocol=WorkspaceServiceProtocol.http,
                url="http://runtime.internal:3000",
                source=WorkspaceServiceSource.runtime_probe,
            )
        ]

    monkeypatch.setattr(
        "app.services.room_workspace_connection_service.get_workspace_service_summaries",
        _mock_get_workspace_service_summaries,
    )

    store = InMemoryContextStore()
    await store.add(
        ContextItem(
            id="service-connection",
            room_id=test_room.room_id,
            agent_slug=None,
            context_type=CURRENT_CONNECTION_CONTEXT_TYPE,
            payload=_current_connection_payload(
                workspace_id=str(workspace.id),
                workspace_name=workspace.name,
                purpose="service_connect",
            ),
            source="system",
            created_at=datetime.now(timezone.utc),
        )
    )

    with pytest.raises(RoomWorkspaceRuntimeTargetResolutionError) as exc_info:
        await consume_current_room_workspace_runtime_target(
            async_session,
            room_id=test_room.room_id,
            context_store=store,
        )

    assert "not configured for agent runtime use" in str(exc_info.value)


@pytest.mark.asyncio
async def test_consume_runtime_target_rejects_expired_current_connection(
    async_session,
    test_room,
    test_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = Workspace(
        id=uuid4(),
        owner_id=test_user.id,
        name="Expired Runtime Workspace",
        status=WorkspaceStatus.ready,
        kennel_name="env-expired",
    )
    async_session.add(workspace)
    await async_session.commit()

    async def _mock_get_workspace_service_summaries(_workspace: Workspace):
        return [
            WorkspaceServiceSummary(
                id="codex",
                kind=WorkspaceServiceKind.agent_runtime,
                label="Codex Runtime",
                status=WorkspaceServiceStatus.ready,
                protocol=WorkspaceServiceProtocol.ws,
                url="ws://runtime.internal:4500",
                source=WorkspaceServiceSource.runtime_probe,
            )
        ]

    monkeypatch.setattr(
        "app.services.room_workspace_connection_service.get_workspace_service_summaries",
        _mock_get_workspace_service_summaries,
    )

    store = InMemoryContextStore()
    await store.add(
        ContextItem(
            id="expired-runtime-connection",
            room_id=test_room.room_id,
            agent_slug=None,
            context_type=CURRENT_CONNECTION_CONTEXT_TYPE,
            payload=_current_connection_payload(
                workspace_id=str(workspace.id),
                workspace_name=workspace.name,
                selected_at=datetime.now(timezone.utc) - timedelta(minutes=11),
            ),
            source="system",
            created_at=datetime.now(timezone.utc),
        )
    )

    with pytest.raises(RoomWorkspaceRuntimeTargetResolutionError) as exc_info:
        await consume_current_room_workspace_runtime_target(
            async_session,
            room_id=test_room.room_id,
            context_store=store,
        )

    assert "has expired" in str(exc_info.value)


@pytest.mark.asyncio
async def test_consume_runtime_target_rejects_connection_without_runtime_endpoint(
    async_session,
    test_room,
    test_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = Workspace(
        id=uuid4(),
        owner_id=test_user.id,
        name="Pending Runtime Workspace",
        status=WorkspaceStatus.ready,
        kennel_name="env-pending",
    )
    async_session.add(workspace)
    await async_session.commit()

    async def _mock_get_workspace_service_summaries(_workspace: Workspace):
        return [
            WorkspaceServiceSummary(
                id="codex",
                kind=WorkspaceServiceKind.agent_runtime,
                label="Codex Runtime",
                status=WorkspaceServiceStatus.ready,
                protocol=WorkspaceServiceProtocol.ws,
                url=None,
                source=WorkspaceServiceSource.runtime_probe,
            )
        ]

    monkeypatch.setattr(
        "app.services.room_workspace_connection_service.get_workspace_service_summaries",
        _mock_get_workspace_service_summaries,
    )

    store = InMemoryContextStore()
    await store.add(
        ContextItem(
            id="pending-runtime-connection",
            room_id=test_room.room_id,
            agent_slug=None,
            context_type=CURRENT_CONNECTION_CONTEXT_TYPE,
            payload=_current_connection_payload(
                workspace_id=str(workspace.id),
                workspace_name=workspace.name,
            ),
            source="system",
            created_at=datetime.now(timezone.utc),
        )
    )

    with pytest.raises(RoomWorkspaceRuntimeTargetResolutionError) as exc_info:
        await consume_current_room_workspace_runtime_target(
            async_session,
            room_id=test_room.room_id,
            context_store=store,
        )

    assert "not yet available" in str(exc_info.value)
