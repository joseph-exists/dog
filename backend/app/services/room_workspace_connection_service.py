from __future__ import annotations

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import get_room_for_user
from app.models import (
    ProjectResource,
    RoomWorkspaceConnectionCapability,
    RoomWorkspaceConnectionDescriptor,
    RoomWorkspaceConnectionPurpose,
    RoomWorkspaceConnectionRequest,
    RoomWorkspaceConnectionStatus,
    RoomWorkspaceEndpointAuthMode,
    RoomWorkspaceEndpointDescriptor,
    RoomWorkspaceEndpointKind,
    User,
    Workspace,
    WorkspaceAction,
    WorkspaceServiceKind,
    WorkspaceServiceStatus,
    WorkspaceStatus,
)
from app.services.workspace_service import (
    get_lifecycle_allowed_actions,
    get_workspace_service_summaries,
)


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
