from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import (
    delete_room_context_item,
    get_room_for_user,
    list_room_context_items,
    upsert_room_context_item,
)
from app.models import (
    ProjectResource,
    RoomWorkspaceCandidate,
    RoomWorkspaceCandidateAccessLevel,
    RoomWorkspaceCandidateRelationship,
    RoomWorkspaceConnectionCapability,
    RoomWorkspaceConnectionDescriptor,
    RoomWorkspaceCurrentConnection,
    RoomWorkspaceCurrentConnectionUpdate,
    RoomWorkspaceConnectionPurpose,
    RoomWorkspaceConnectionRequest,
    RoomWorkspaceConnectionStatus,
    RoomContextItemCreate,
    RoomWorkspaceEndpointAuthMode,
    RoomWorkspaceEndpointDescriptor,
    RoomWorkspaceEndpointKind,
    User,
    Workspace,
    WorkspaceAction,
    WorkspaceServiceKind,
    WorkspaceServiceStatus,
    WorkspaceStatus,
    WorkspaceVisibility,
)
from app.services.workspace_service import (
    get_allowed_actions_for_user,
    get_lifecycle_allowed_actions,
    get_workspace_project_summary,
    list_workspaces_visible_to_user,
    get_workspace_service_summaries,
)

CURRENT_CONNECTION_CONTEXT_ID = "room-workspace-current-connection"
CURRENT_CONNECTION_CONTEXT_TYPE = "system.room.workspace.current_connection"
CURRENT_CONNECTION_CONTEXT_SOURCE = "room_workspace_connection"
CURRENT_CONNECTION_TTL = timedelta(minutes=10)


async def _get_project_ids_for_resource(
    session: AsyncSession,
    *,
    resource_type: str,
    resource_id: UUID,
) -> set[UUID]:
    stmt = select(ProjectResource.project_id).where(
        ProjectResource.resource_type == resource_type,
        ProjectResource.resource_id == resource_id,
    )
    return set((await session.exec(stmt)).all())


def _capabilities_for_workspace_services(workspace_services) -> list[RoomWorkspaceConnectionCapability]:
    capabilities: list[RoomWorkspaceConnectionCapability] = []
    if any(service.kind != WorkspaceServiceKind.agent_runtime for service in workspace_services):
        capabilities.append(RoomWorkspaceConnectionCapability.service_connect)
    if any(service.kind == WorkspaceServiceKind.agent_runtime for service in workspace_services):
        capabilities.append(RoomWorkspaceConnectionCapability.agent_runtime_connect)
    return capabilities


def _candidate_access_level_from_actions(
    *,
    allowed_actions: list[WorkspaceAction],
) -> RoomWorkspaceCandidateAccessLevel:
    manage_actions = {
        WorkspaceAction.start,
        WorkspaceAction.stop,
        WorkspaceAction.destroy,
    }
    if any(action in manage_actions for action in allowed_actions):
        return RoomWorkspaceCandidateAccessLevel.manage
    if any(
        action in {WorkspaceAction.request_terminal, WorkspaceAction.discover_services}
        for action in allowed_actions
    ):
        return RoomWorkspaceCandidateAccessLevel.use
    return RoomWorkspaceCandidateAccessLevel.view


def _build_endpoint_scope(
    *,
    room_id: UUID,
    workspace_id: UUID,
    purpose: RoomWorkspaceConnectionPurpose,
    endpoint_id: str,
) -> dict[str, str]:
    return {
        "room_id": str(room_id),
        "workspace_id": str(workspace_id),
        "purpose": purpose.value,
        "endpoint_id": endpoint_id,
    }


def _coerce_relationship(value: object) -> RoomWorkspaceCandidateRelationship:
    if value == RoomWorkspaceCandidateRelationship.owner_private.value:
        return RoomWorkspaceCandidateRelationship.owner_private
    return RoomWorkspaceCandidateRelationship.shared_project


def _coerce_access_level(value: object) -> RoomWorkspaceCandidateAccessLevel:
    if value == RoomWorkspaceCandidateAccessLevel.manage.value:
        return RoomWorkspaceCandidateAccessLevel.manage
    if value == RoomWorkspaceCandidateAccessLevel.use.value:
        return RoomWorkspaceCandidateAccessLevel.use
    return RoomWorkspaceCandidateAccessLevel.view


def _coerce_selected_at(value: object) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _current_connection_payload(
    *,
    candidate: RoomWorkspaceCandidate,
    purpose: RoomWorkspaceConnectionPurpose,
    selected_at: datetime,
) -> dict[str, object]:
    return {
        "workspace_id": str(candidate.workspace_id),
        "workspace_name": candidate.workspace_name,
        "purpose": purpose.value,
        "relationship": candidate.relationship.value,
        "access_level": candidate.access_level.value,
        "service_count": candidate.service_count,
        "ready_service_count": candidate.ready_service_count,
        "selected_at": selected_at.isoformat(),
    }


async def _find_current_connection_context(
    session: AsyncSession,
    *,
    current_user: User,
    room_id: UUID,
):
    contexts = await list_room_context_items(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )
    for item in contexts.data:
        if item.context_type == CURRENT_CONNECTION_CONTEXT_TYPE:
            return item
    return None


async def list_room_workspace_candidates(
    session: AsyncSession,
    *,
    current_user: User,
    room_id: UUID,
) -> list[RoomWorkspaceCandidate]:
    room = await get_room_for_user(room_id=room_id, user_id=current_user.id, session=session)
    visible_workspaces = await list_workspaces_visible_to_user(session, user=current_user)
    room_project_ids = await _get_project_ids_for_resource(
        session,
        resource_type="room",
        resource_id=room.room_id,
    )

    candidates: list[RoomWorkspaceCandidate] = []
    for workspace in visible_workspaces:
        workspace_project_ids = await _get_project_ids_for_resource(
            session,
            resource_type="workspace",
            resource_id=workspace.id,
        )
        shared_project_ids = room_project_ids & workspace_project_ids
        owner_private_allowed = (
            room.creator_id == current_user.id and workspace.owner_id == current_user.id
        )

        if shared_project_ids:
            relationship = RoomWorkspaceCandidateRelationship.shared_project
            rank = 100
            match_reason = "Room and workspace share project access."
        elif owner_private_allowed:
            relationship = RoomWorkspaceCandidateRelationship.owner_private
            rank = 50
            match_reason = "Owner-private fallback is available for this room and workspace."
        else:
            continue

        services = await get_workspace_service_summaries(workspace)
        ready_service_count = sum(
            1 for service in services if service.status == WorkspaceServiceStatus.ready
        )
        allowed_actions = await get_allowed_actions_for_user(
            session,
            workspace=workspace,
            user=current_user,
        )
        access_level = _candidate_access_level_from_actions(
            allowed_actions=allowed_actions,
        )
        project_summary = await get_workspace_project_summary(session, workspace.id)

        candidates.append(
            RoomWorkspaceCandidate(
                room_id=room.room_id,
                workspace_id=workspace.id,
                workspace_name=workspace.name,
                workspace_status=workspace.status,
                visibility=(
                    WorkspaceVisibility.project
                    if project_summary is not None
                    else WorkspaceVisibility.private
                ),
                project_id=project_summary.id if project_summary is not None else None,
                project_summary=project_summary,
                relationship=relationship,
                access_level=access_level,
                match_reason=match_reason,
                candidate_rank=rank,
                service_count=len(services),
                ready_service_count=ready_service_count,
                supports_service_connect=any(
                    service.kind != WorkspaceServiceKind.agent_runtime for service in services
                ),
                supports_agent_runtime_connect=any(
                    service.kind == WorkspaceServiceKind.agent_runtime for service in services
                ),
            )
        )

    candidates.sort(
        key=lambda candidate: (
            -candidate.candidate_rank,
            -candidate.ready_service_count,
            -candidate.service_count,
            candidate.workspace_name.lower(),
        )
    )
    return candidates


async def build_room_workspace_connection_descriptor(
    session: AsyncSession,
    *,
    current_user: User,
    room_id: UUID,
    request: RoomWorkspaceConnectionRequest,
) -> RoomWorkspaceConnectionDescriptor:
    room = await get_room_for_user(room_id=room_id, user_id=current_user.id, session=session)
    workspace = await session.get(Workspace, request.workspace_id)
    if workspace is None:
        return RoomWorkspaceConnectionDescriptor(
            room_id=room_id,
            workspace_id=request.workspace_id,
            purpose=request.purpose,
            status=RoomWorkspaceConnectionStatus.denied,
            reason="Workspace not found.",
        )

    room_project_ids = await _get_project_ids_for_resource(
        session,
        resource_type="room",
        resource_id=room.room_id,
    )
    workspace_project_ids = await _get_project_ids_for_resource(
        session,
        resource_type="workspace",
        resource_id=workspace.id,
    )

    shared_project_ids = room_project_ids & workspace_project_ids
    owner_private_allowed = room.creator_id == current_user.id and workspace.owner_id == current_user.id

    if not (current_user.is_superuser or shared_project_ids or owner_private_allowed):
        return RoomWorkspaceConnectionDescriptor(
            room_id=room.room_id,
            workspace_id=workspace.id,
            purpose=request.purpose,
            status=RoomWorkspaceConnectionStatus.denied,
            reason="Room does not have an authorized path to this workspace.",
        )

    if workspace.status in {WorkspaceStatus.destroying, WorkspaceStatus.destroyed, WorkspaceStatus.failed}:
        return RoomWorkspaceConnectionDescriptor(
            room_id=room.room_id,
            workspace_id=workspace.id,
            purpose=request.purpose,
            status=RoomWorkspaceConnectionStatus.denied,
            reason=f"Workspace is not connectable in state '{workspace.status.value}'.",
        )

    allowed_actions = get_lifecycle_allowed_actions(workspace)
    if WorkspaceAction.discover_services not in allowed_actions:
        return RoomWorkspaceConnectionDescriptor(
            room_id=room.room_id,
            workspace_id=workspace.id,
            purpose=request.purpose,
            status=RoomWorkspaceConnectionStatus.pending,
            reason="Workspace is not yet exposing discoverable runtime services.",
        )

    services = await get_workspace_service_summaries(workspace)
    capabilities = _capabilities_for_workspace_services(services)

    if request.purpose == RoomWorkspaceConnectionPurpose.service_connect:
        matching_services = [
            service
            for service in services
            if service.kind != WorkspaceServiceKind.agent_runtime
        ]
        endpoint_kind = RoomWorkspaceEndpointKind.service
    else:
        matching_services = [
            service
            for service in services
            if service.kind == WorkspaceServiceKind.agent_runtime
        ]
        endpoint_kind = RoomWorkspaceEndpointKind.agent_runtime

    if not matching_services:
        return RoomWorkspaceConnectionDescriptor(
            room_id=room.room_id,
            workspace_id=workspace.id,
            purpose=request.purpose,
            status=RoomWorkspaceConnectionStatus.denied,
            reason="No discovered runtime surfaces match the requested connection purpose.",
            capabilities=capabilities,
        )

    ready_routable_services = [
        service
        for service in matching_services
        if service.status == WorkspaceServiceStatus.ready and service.url
    ]
    ready_unroutable_services = [
        service
        for service in matching_services
        if service.status == WorkspaceServiceStatus.ready and not service.url
    ]
    pending_services = [
        service
        for service in matching_services
        if service.status in {WorkspaceServiceStatus.pending, WorkspaceServiceStatus.unknown}
    ]

    if ready_routable_services:
        return RoomWorkspaceConnectionDescriptor(
            room_id=room.room_id,
            workspace_id=workspace.id,
            purpose=request.purpose,
            status=RoomWorkspaceConnectionStatus.available,
            reason=None,
            capabilities=capabilities,
            endpoints=[
                RoomWorkspaceEndpointDescriptor(
                    id=service.id,
                    kind=endpoint_kind,
                    label=service.label,
                    protocol=service.protocol.value,
                    url=service.url,
                    auth_mode=RoomWorkspaceEndpointAuthMode.none,
                    expires_at=None,
                    scope=_build_endpoint_scope(
                        room_id=room.room_id,
                        workspace_id=workspace.id,
                        purpose=request.purpose,
                        endpoint_id=service.id,
                    ),
                )
                for service in ready_routable_services
            ],
        )

    if ready_unroutable_services or pending_services:
        return RoomWorkspaceConnectionDescriptor(
            room_id=room.room_id,
            workspace_id=workspace.id,
            purpose=request.purpose,
            status=RoomWorkspaceConnectionStatus.pending,
            reason=(
                "Matching runtime is healthy, but no routed connection endpoint has been issued yet."
                if ready_unroutable_services
                else "Matching runtime surfaces are still starting or awaiting live discovery."
            ),
            capabilities=capabilities,
            endpoints=[
                RoomWorkspaceEndpointDescriptor(
                    id=service.id,
                    kind=endpoint_kind,
                    label=service.label,
                    protocol=service.protocol.value,
                    url=service.url,
                    auth_mode=RoomWorkspaceEndpointAuthMode.none,
                    expires_at=None,
                    scope=_build_endpoint_scope(
                        room_id=room.room_id,
                        workspace_id=workspace.id,
                        purpose=request.purpose,
                        endpoint_id=service.id,
                    ),
                )
                for service in matching_services
                if service.url
            ],
        )

    return RoomWorkspaceConnectionDescriptor(
        room_id=room.room_id,
        workspace_id=workspace.id,
        purpose=request.purpose,
        status=RoomWorkspaceConnectionStatus.denied,
        reason="No matching runtime surfaces are currently available for this connection purpose.",
        capabilities=capabilities,
    )


async def get_current_room_workspace_connection(
    session: AsyncSession,
    *,
    current_user: User,
    room_id: UUID,
) -> RoomWorkspaceCurrentConnection | None:
    context_item = await _find_current_connection_context(
        session,
        current_user=current_user,
        room_id=room_id,
    )
    if context_item is None:
        return None

    payload = context_item.payload if isinstance(context_item.payload, dict) else {}
    workspace_id_raw = payload.get("workspace_id")
    purpose_raw = payload.get("purpose")
    if not isinstance(workspace_id_raw, str) or not isinstance(purpose_raw, str):
        return None

    try:
        workspace_id = UUID(workspace_id_raw)
        purpose = RoomWorkspaceConnectionPurpose(purpose_raw)
    except (ValueError, TypeError):
        return None

    descriptor = await build_room_workspace_connection_descriptor(
        session,
        current_user=current_user,
        room_id=room_id,
        request=RoomWorkspaceConnectionRequest(
            workspace_id=workspace_id,
            purpose=purpose,
        ),
    )

    workspace = await session.get(Workspace, workspace_id)
    workspace_name = (
        str(payload.get("workspace_name"))
        if isinstance(payload.get("workspace_name"), str)
        else (workspace.name if workspace is not None else "Unknown workspace")
    )

    return RoomWorkspaceCurrentConnection(
        room_id=room_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        purpose=purpose,
        relationship=_coerce_relationship(payload.get("relationship")),
        access_level=_coerce_access_level(payload.get("access_level")),
        selected_at=_coerce_selected_at(payload.get("selected_at")),
        service_count=(
            payload.get("service_count")
            if isinstance(payload.get("service_count"), int)
            else 0
        ),
        ready_service_count=(
            payload.get("ready_service_count")
            if isinstance(payload.get("ready_service_count"), int)
            else 0
        ),
        descriptor=descriptor,
    )


async def set_current_room_workspace_connection(
    session: AsyncSession,
    *,
    current_user: User,
    room_id: UUID,
    request: RoomWorkspaceCurrentConnectionUpdate,
) -> RoomWorkspaceCurrentConnection:
    candidates = await list_room_workspace_candidates(
        session,
        current_user=current_user,
        room_id=room_id,
    )
    candidate = next(
        (item for item in candidates if item.workspace_id == request.workspace_id),
        None,
    )
    if candidate is None:
        raise HTTPException(
            status_code=403,
            detail="Workspace is not available as a room-aware candidate.",
        )

    descriptor = await build_room_workspace_connection_descriptor(
        session,
        current_user=current_user,
        room_id=room_id,
        request=RoomWorkspaceConnectionRequest(
            workspace_id=request.workspace_id,
            purpose=request.purpose,
        ),
    )
    if descriptor.status == RoomWorkspaceConnectionStatus.denied:
        raise HTTPException(
            status_code=403,
            detail=descriptor.reason or "Workspace connection is not allowed.",
        )

    selected_at = datetime.now(timezone.utc)
    context_item = await upsert_room_context_item(
        room_id=room_id,
        user_id=current_user.id,
        context_id=CURRENT_CONNECTION_CONTEXT_ID,
        context_in=RoomContextItemCreate(
            context_type=CURRENT_CONNECTION_CONTEXT_TYPE,
            payload=_current_connection_payload(
                candidate=candidate,
                purpose=request.purpose,
                selected_at=selected_at,
            ),
            source=CURRENT_CONNECTION_CONTEXT_SOURCE,
            expires_at=selected_at + CURRENT_CONNECTION_TTL,
        ),
        replace_by_type=True,
        session=session,
    )

    return RoomWorkspaceCurrentConnection(
        room_id=room_id,
        workspace_id=candidate.workspace_id,
        workspace_name=candidate.workspace_name,
        purpose=request.purpose,
        relationship=candidate.relationship,
        access_level=candidate.access_level,
        selected_at=context_item.created_at,
        service_count=candidate.service_count,
        ready_service_count=candidate.ready_service_count,
        descriptor=descriptor,
    )


async def clear_current_room_workspace_connection(
    session: AsyncSession,
    *,
    current_user: User,
    room_id: UUID,
) -> None:
    context_item = await _find_current_connection_context(
        session,
        current_user=current_user,
        room_id=room_id,
    )
    if context_item is None:
        return

    await delete_room_context_item(
        room_id=room_id,
        user_id=current_user.id,
        context_id=context_item.id,
        session=session,
    )
