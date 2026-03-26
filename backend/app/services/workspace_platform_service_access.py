from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    User,
    Workspace,
    WorkspaceAction,
    WorkspacePlatformServiceAccessGrant,
    WorkspacePlatformServiceConsumerKind,
    WorkspacePlatformServiceGrant,
    WorkspacePlatformServiceGrantRequest,
    WorkspaceRuntimePlatformConfig,
)
from app.services.mcp_registry import (
    get_mcp_server_descriptor,
    list_mcp_server_descriptors,
)

PLATFORM_SERVICE_GRANT_TTL = timedelta(minutes=10)
ENV_PREFIX_BY_CONSUMER: dict[WorkspacePlatformServiceConsumerKind, str] = {
    WorkspacePlatformServiceConsumerKind.workspace_runtime: "DOG_PLATFORM",
    WorkspacePlatformServiceConsumerKind.agent_runtime: "DOG_AGENT_PLATFORM",
}


@dataclass(frozen=True)
class WorkspacePlatformEnvProjection:
    """Runtime-facing environment projection derived from canonical config."""

    consumer_kind: WorkspacePlatformServiceConsumerKind
    config: WorkspaceRuntimePlatformConfig
    env_vars: dict[str, str]
    runtime_files: dict[str, str]


def _build_service_scope(
    *,
    workspace_id: str,
    service_id: str,
    consumer_kind: WorkspacePlatformServiceConsumerKind,
    grant_id: str,
) -> dict[str, str]:
    return {
        "workspace_id": workspace_id,
        "service_id": service_id,
        "consumer_kind": consumer_kind.value,
        "grant_id": grant_id,
    }


def _service_env_token(service_id: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", service_id.upper()).strip("_")


def _runtime_projection_path(*, consumer_kind: WorkspacePlatformServiceConsumerKind) -> str:
    if consumer_kind == WorkspacePlatformServiceConsumerKind.agent_runtime:
        return "/home/dev/.dog/platform-services/agent-runtime.json"
    return "/home/dev/.dog/platform-services/workspace-runtime.json"


def _select_platform_service_descriptors(
    *,
    service_ids: list[str],
):
    requested_service_ids = {
        service_id.strip()
        for service_id in service_ids
        if isinstance(service_id, str) and service_id.strip()
    }
    if requested_service_ids:
        descriptors = []
        for service_id in requested_service_ids:
            descriptor = get_mcp_server_descriptor(service_id)
            if descriptor is None or not descriptor.enabled:
                raise ValueError(f"Platform service '{service_id}' is not available")
            descriptors.append(descriptor)
        return descriptors
    return list_mcp_server_descriptors()


async def _ensure_workspace_platform_access_allowed(
    db: AsyncSession,
    *,
    workspace: Workspace,
    user: User,
) -> None:
    from app.services import workspace_service

    lifecycle_actions = workspace_service.get_lifecycle_allowed_actions(workspace)
    if WorkspaceAction.discover_services not in lifecycle_actions:
        raise ValueError(f"Workspace not ready: {workspace.status}")

    allowed_actions = await workspace_service.get_allowed_actions_for_user(
        db,
        workspace=workspace,
        user=user,
    )
    if WorkspaceAction.discover_services not in allowed_actions:
        raise PermissionError("Workspace platform service access is not allowed")


def _build_platform_service_grants(
    *,
    workspace: Workspace,
    consumer_kind: WorkspacePlatformServiceConsumerKind,
    descriptors,
    issued_at: datetime,
    expires_at: datetime,
) -> list[WorkspacePlatformServiceGrant]:
    workspace_id_str = str(workspace.id)
    services: list[WorkspacePlatformServiceGrant] = []
    for descriptor in descriptors:
        grant_id = str(uuid4())
        services.append(
            WorkspacePlatformServiceGrant(
                grant_id=grant_id,
                service_id=descriptor.id,
                transport=descriptor.transport,
                url=descriptor.url,
                auth_mode="none",
                require_approval=descriptor.require_approval_default,
                description=descriptor.description,
                scopes=list(descriptor.scopes),
                tags=list(descriptor.tags),
                scope=_build_service_scope(
                    workspace_id=workspace_id_str,
                    service_id=descriptor.id,
                    consumer_kind=consumer_kind,
                    grant_id=grant_id,
                ),
                issued_at=issued_at,
                expires_at=expires_at,
            )
        )
    return services


def _build_runtime_platform_config_for_workspace(
    *,
    workspace: Workspace,
    consumer_kind: WorkspacePlatformServiceConsumerKind,
    service_ids: list[str],
) -> WorkspaceRuntimePlatformConfig:
    descriptors = _select_platform_service_descriptors(service_ids=service_ids)
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + PLATFORM_SERVICE_GRANT_TTL
    services = _build_platform_service_grants(
        workspace=workspace,
        consumer_kind=consumer_kind,
        descriptors=descriptors,
        issued_at=issued_at,
        expires_at=expires_at,
    )
    return WorkspaceRuntimePlatformConfig(
        workspace_id=workspace.id,
        consumer_kind=consumer_kind,
        issued_at=issued_at,
        expires_at=expires_at,
        services=services,
    )


def build_workspace_platform_env_projection_for_workspace(
    *,
    workspace: Workspace,
    consumer_kind: WorkspacePlatformServiceConsumerKind,
    service_ids: list[str] | None = None,
) -> WorkspacePlatformEnvProjection:
    config = _build_runtime_platform_config_for_workspace(
        workspace=workspace,
        consumer_kind=consumer_kind,
        service_ids=service_ids or [],
    )
    prefix = ENV_PREFIX_BY_CONSUMER[consumer_kind]
    runtime_file_path = _runtime_projection_path(consumer_kind=consumer_kind)
    runtime_files = {
        runtime_file_path: json.dumps(config.model_dump(mode="json")),
    }
    env_vars: dict[str, str] = {
        f"{prefix}_SERVICES_JSON": json.dumps(config.model_dump(mode="json")),
        f"{prefix}_SERVICES_PATH": runtime_file_path,
        f"{prefix}_SERVICE_ACCESS_ISSUED_AT": config.issued_at.isoformat(),
        f"{prefix}_SERVICE_ACCESS_EXPIRES_AT": (
            config.expires_at.isoformat() if config.expires_at else ""
        ),
        f"{prefix}_SERVICE_COUNT": str(len(config.services)),
    }
    for service in config.services:
        token = _service_env_token(service.service_id)
        env_vars[f"{prefix}_SERVICE_{token}_URL"] = service.url
        env_vars[f"{prefix}_SERVICE_{token}_TRANSPORT"] = service.transport
        env_vars[f"{prefix}_SERVICE_{token}_AUTH_MODE"] = service.auth_mode
        env_vars[f"{prefix}_SERVICE_{token}_GRANT_ID"] = service.grant_id
        env_vars[f"{prefix}_SERVICE_{token}_SCOPES"] = ",".join(service.scopes)
        env_vars[f"{prefix}_SERVICE_{token}_TAGS"] = ",".join(service.tags)
    return WorkspacePlatformEnvProjection(
        consumer_kind=consumer_kind,
        config=config,
        env_vars=env_vars,
        runtime_files=runtime_files,
    )


async def issue_workspace_platform_service_access(
    db: AsyncSession,
    *,
    workspace_id,
    user: User,
    request: WorkspacePlatformServiceGrantRequest,
) -> WorkspacePlatformServiceAccessGrant:
    from app.services import workspace_service

    workspace = await workspace_service.get_workspace_for_user(
        db,
        workspace_id=workspace_id,
        user=user,
    )
    if workspace is None:
        raise ValueError("Workspace not found")
    return await issue_workspace_platform_service_access_for_workspace(
        db,
        workspace=workspace,
        user=user,
        request=request,
    )


async def issue_workspace_platform_service_access_for_workspace(
    db: AsyncSession,
    *,
    workspace: Workspace,
    user: User,
    request: WorkspacePlatformServiceGrantRequest,
) -> WorkspacePlatformServiceAccessGrant:
    await _ensure_workspace_platform_access_allowed(
        db,
        workspace=workspace,
        user=user,
    )
    config = _build_runtime_platform_config_for_workspace(
        workspace=workspace,
        consumer_kind=request.consumer_kind,
        service_ids=request.service_ids,
    )
    return WorkspacePlatformServiceAccessGrant(
        workspace_id=config.workspace_id,
        consumer_kind=config.consumer_kind,
        issued_at=config.issued_at,
        expires_at=config.expires_at,
        services=config.services,
    )


async def resolve_workspace_runtime_platform_config(
    db: AsyncSession,
    *,
    workspace_id,
    user: User,
    request: WorkspacePlatformServiceGrantRequest,
) -> WorkspaceRuntimePlatformConfig:
    from app.services import workspace_service

    workspace = await workspace_service.get_workspace_for_user(
        db,
        workspace_id=workspace_id,
        user=user,
    )
    if workspace is None:
        raise ValueError("Workspace not found")
    return await resolve_workspace_runtime_platform_config_for_workspace(
        db,
        workspace=workspace,
        user=user,
        request=request,
    )


async def resolve_workspace_runtime_platform_config_for_workspace(
    db: AsyncSession,
    *,
    workspace: Workspace,
    user: User,
    request: WorkspacePlatformServiceGrantRequest,
) -> WorkspaceRuntimePlatformConfig:
    await _ensure_workspace_platform_access_allowed(
        db,
        workspace=workspace,
        user=user,
    )
    return _build_runtime_platform_config_for_workspace(
        workspace=workspace,
        consumer_kind=request.consumer_kind,
        service_ids=request.service_ids,
    )


async def refresh_workspace_runtime_platform_projection(
    db: AsyncSession,
    *,
    workspace_id,
    user: User,
    request: WorkspacePlatformServiceGrantRequest,
) -> WorkspacePlatformEnvProjection:
    from app.services import workspace_service

    workspace = await workspace_service.get_workspace_for_user(
        db,
        workspace_id=workspace_id,
        user=user,
    )
    if workspace is None:
        raise ValueError("Workspace not found")
    await _ensure_workspace_platform_access_allowed(
        db,
        workspace=workspace,
        user=user,
    )
    return build_workspace_platform_env_projection_for_workspace(
        workspace=workspace,
        consumer_kind=request.consumer_kind,
        service_ids=request.service_ids,
    )
