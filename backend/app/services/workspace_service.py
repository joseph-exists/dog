import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import async_session_maker
from app.models import (
    AccessGrantRole,
    Project,
    ProjectResource,
    User,
    UserRepo,
    UserRepoImportStatus,
    Workspace,
    WorkspaceAction,
    WorkspaceBootstrapIntent,
    WorkspaceBootstrapPhase,
    WorkspaceBootstrapProgress,
    WorkspaceBootstrapState,
    WorkspaceCreate,
    WorkspaceConnectivitySummary,
    WorkspaceExternalUrlRepoSource,
    WorkspaceFlavourHealthSummary,
    WorkspaceInstallIntentNone,
    WorkspaceProjectSummary,
    WorkspacePublic,
    WorkspaceReadinessSummary,
    WorkspaceServiceKind,
    WorkspaceServiceProtocol,
    WorkspaceServiceSource,
    WorkspaceServiceStatus,
    WorkspaceServiceSummary,
    WorkspaceShadowRepoSource,
    WorkspaceStatus,
    WorkspaceStartupIntentTerminalOnly,
    WorkspaceTerminalStatus,
    WorkspaceUserRepoSource,
    WorkspaceVisibility,
    WorkspacePlatformServiceConsumerKind,
)
from app.services import kennel_client
from app.services.access_control import get_effective_role, has_access
from app.services.workspace_bootstrap_service import (
    WorkspaceBootstrapPlan,
    WorkspaceBootstrapValidationError,
    generate_bootstrap_plan,
)
from app.services.workspace_platform_service_access import (
    build_workspace_platform_env_projection_for_workspace,
)

log = logging.getLogger(__name__)
_FLAVOUR_CACHE_TTL_SECONDS = 30.0
_flavour_cache: tuple[float, dict[str, dict]] | None = None


@dataclass(frozen=True)
class NormalizedWorkspaceBootstrap:
    """
    Normalized bootstrap state for the current implementation slice.

    This structure is intentionally small and operational:
    - `intent` preserves the user-facing typed contract
    - `materialized_repo_url` is the repo URL the current kennel injection path can use

    We expect this to evolve into a richer backend-generated execution plan in
    the next Track 2 steps. Keeping it explicit now gives future engineers a
    clear place to extend behavior without unwinding the request contract.
    """

    intent: WorkspaceBootstrapIntent
    materialized_repo_url: str | None
    plan: WorkspaceBootstrapPlan


@dataclass(frozen=True)
class FlavourHealthSnapshot:
    snapshot_ready: bool
    latest_rebuild_status: str | None
    latest_rebuild_job_id: str | None


async def spawn_workspace(
    db: AsyncSession,
    owner_id: uuid.UUID,
    req: WorkspaceCreate,
) -> Workspace:
    """
    Create the workspace record and start kennel provisioning asynchronously.
    """
    kennel_name = f"env-{uuid.uuid4().hex[:8]}"
    normalized_bootstrap = await normalize_bootstrap_intent(
        db,
        owner_id=owner_id,
        req=req,
    )

    workspace = Workspace(
        name=req.name,
        flavour=req.flavour,
        kind=req.kind,
        owner_id=owner_id,
        kennel_name=kennel_name,
        status=WorkspaceStatus.requested,
        meta={
            "repo_url": normalized_bootstrap.materialized_repo_url,
            "ssh_pubkey": normalized_bootstrap.intent.ssh_pubkey,
            "env_vars": normalized_bootstrap.intent.env_vars,
            "bootstrap_intent": normalized_bootstrap.intent.model_dump(mode="json"),
            "bootstrap_plan": normalized_bootstrap.plan.model_dump(mode="json"),
            "bootstrap_progress": WorkspaceBootstrapProgress(
                phase=WorkspaceBootstrapPhase.pending,
                message="Bootstrap intent accepted.",
                step_count=len(normalized_bootstrap.plan.steps),
                completed_steps=0,
            ).model_dump(mode="json"),
        },
    )
    db.add(workspace)
    await db.flush()
    await db.refresh(workspace)

    asyncio.create_task(
        _provision_workspace_after_commit(
            ws_id=workspace.id,
            kennel_name=kennel_name,
            workspace_kind=req.kind,
            workspace_flavour=req.flavour.value,
            bootstrap_intent=normalized_bootstrap.intent,
            resolved_repo_url=normalized_bootstrap.materialized_repo_url,
            bootstrap_plan=normalized_bootstrap.plan,
        )
    )

    return workspace


async def _provision_workspace_after_commit(
    ws_id: uuid.UUID,
    kennel_name: str,
    workspace_kind: str,
    workspace_flavour: str,
    bootstrap_intent: WorkspaceBootstrapIntent,
    resolved_repo_url: str | None,
    bootstrap_plan: WorkspaceBootstrapPlan,
) -> None:
    """
    Yield once so the request-scoped transaction can finish before
    background provisioning starts using its own session.
    """
    await asyncio.sleep(0)
    await _provision_workspace(
        ws_id=ws_id,
        kennel_name=kennel_name,
        workspace_kind=workspace_kind,
        workspace_flavour=workspace_flavour,
        bootstrap_intent=bootstrap_intent,
        resolved_repo_url=resolved_repo_url,
        bootstrap_plan=bootstrap_plan,
    )


async def _provision_workspace(
    ws_id: uuid.UUID,
    kennel_name: str,
    workspace_kind: str,
    workspace_flavour: str,
    bootstrap_intent: WorkspaceBootstrapIntent,
    resolved_repo_url: str | None,
    bootstrap_plan: WorkspaceBootstrapPlan,
) -> None:
    """
    Drive the kennel lifecycle: create -> poll -> inject -> mark ready.
    """
    try:
        job = await kennel_client.create_env(
            name=kennel_name,
            kind=bootstrap_kind_from_intent(bootstrap_intent) or workspace_kind,
            flavour=bootstrap_flavour_from_intent(bootstrap_intent) or workspace_flavour,
        )
        job_id = job["job_id"]
        await _update_workspace(
            ws_id,
            status=WorkspaceStatus.provisioning,
            kennel_job=job_id,
            failure_message=None,
            bootstrap_progress=WorkspaceBootstrapProgress(
                phase=WorkspaceBootstrapPhase.resolving_source,
                message="Provisioning environment and resolving bootstrap source.",
                step_count=len(bootstrap_plan.steps),
                completed_steps=0,
            ),
        )

        log.info("[workspace:%s] kennel job %s started", ws_id, job_id)

        result = await _poll_until_done(job_id, timeout=600)
        if result["status"] == "failed":
            await _update_workspace(
                ws_id,
                status=WorkspaceStatus.failed,
                failure_message=result.get("error") or "Workspace provisioning failed.",
            )
            return

        await _update_workspace(
            ws_id,
            status=WorkspaceStatus.starting,
            bootstrap_progress=WorkspaceBootstrapProgress(
                phase=(
                    bootstrap_plan.steps[0].phase
                    if bootstrap_plan.steps
                    else WorkspaceBootstrapPhase.running_readiness_checks
                ),
                message=(
                    f"Executing bootstrap plan with {len(bootstrap_plan.steps)} step(s)."
                    if bootstrap_plan.steps
                    else "No bootstrap steps required; issuing terminal access."
                ),
                step_count=len(bootstrap_plan.steps),
                completed_steps=0,
            ),
        )

        projected_env_vars = dict(bootstrap_intent.env_vars or {})
        platform_service_projection_summary: list[dict[str, object]] = []
        async with async_session_maker() as projection_session:
            projection_workspace = await projection_session.get(Workspace, ws_id)
            if projection_workspace is None:
                raise RuntimeError("Workspace disappeared before platform projection.")

            workspace_runtime_projection = build_workspace_platform_env_projection_for_workspace(
                workspace=projection_workspace,
                consumer_kind=WorkspacePlatformServiceConsumerKind.workspace_runtime,
            )
            projected_env_vars.update(workspace_runtime_projection.env_vars)
            platform_service_projection_summary.append(
                {
                    "consumer_kind": workspace_runtime_projection.consumer_kind.value,
                    "service_ids": [
                        service.service_id for service in workspace_runtime_projection.config.services
                    ],
                    "issued_at": workspace_runtime_projection.config.issued_at.isoformat(),
                    "expires_at": (
                        workspace_runtime_projection.config.expires_at.isoformat()
                        if workspace_runtime_projection.config.expires_at
                        else None
                    ),
                }
            )

            startup_intent = bootstrap_intent.startup_intent
            if getattr(startup_intent, "mode", None) == "agent_service":
                agent_runtime_projection = build_workspace_platform_env_projection_for_workspace(
                    workspace=projection_workspace,
                    consumer_kind=WorkspacePlatformServiceConsumerKind.agent_runtime,
                )
                projected_env_vars.update(agent_runtime_projection.env_vars)
                platform_service_projection_summary.append(
                    {
                        "consumer_kind": agent_runtime_projection.consumer_kind.value,
                        "service_ids": [
                            service.service_id for service in agent_runtime_projection.config.services
                        ],
                        "issued_at": agent_runtime_projection.config.issued_at.isoformat(),
                        "expires_at": (
                            agent_runtime_projection.config.expires_at.isoformat()
                            if agent_runtime_projection.config.expires_at
                            else None
                        ),
                    }
                )

        inject_result = await kennel_client.inject_workspace(
            kennel_name,
            {
                "user": "dev",
                "ssh_pubkey": bootstrap_intent.ssh_pubkey,
                "repo_url": resolved_repo_url,
                "env_vars": projected_env_vars,
                "bootstrap_plan": bootstrap_plan.model_dump(mode="json"),
            },
        )

        completed_step_count = len(
            [
                step
                for step in inject_result.get("step_results", [])
                if step.get("status") == "completed"
            ]
        )
        bootstrap_success = bool(inject_result.get("bootstrap_success", True))
        bootstrap_failure_message = inject_result.get("fatal_error")
        workspace_meta_updates = {
            "inject_errors": inject_result.get("errors", []),
            "declared_services": inject_result.get("declared_services", []),
            "bootstrap_step_results": inject_result.get("step_results", []),
            "bootstrap_started_services": inject_result.get("started_services", []),
            "bootstrap_workspace_path": inject_result.get("workspace_path"),
            "platform_service_projection": platform_service_projection_summary,
        }

        if not bootstrap_success:
            await _update_workspace(
                ws_id,
                status=WorkspaceStatus.failed,
                failure_message=bootstrap_failure_message or "Workspace bootstrap failed.",
                bootstrap_progress=WorkspaceBootstrapProgress(
                    phase=WorkspaceBootstrapPhase.failed,
                    message="Bootstrap plan execution failed.",
                    step_count=len(bootstrap_plan.steps),
                    completed_steps=completed_step_count,
                    failure_message=bootstrap_failure_message,
                ),
                meta_updates=workspace_meta_updates,
            )
            return

        await _update_workspace(
            ws_id,
            status=WorkspaceStatus.ready,
            ws_token=inject_result.get("token"),
            failure_message=None,
            bootstrap_progress=WorkspaceBootstrapProgress(
                phase=WorkspaceBootstrapPhase.complete,
                message="Bootstrap completed successfully.",
                step_count=len(bootstrap_plan.steps),
                completed_steps=len(bootstrap_plan.steps),
            ),
            meta_updates=workspace_meta_updates,
        )

        log.info(
            "[workspace:%s] ready at %s",
            ws_id,
            kennel_client.terminal_url(
                kennel_name,
                inject_result["token"],
            ),
        )
    except Exception as exc:
        log.exception("[workspace:%s] provisioning failed: %s", ws_id, exc)
        await _update_workspace(
            ws_id,
            status=WorkspaceStatus.failed,
            failure_message=str(exc),
            bootstrap_progress=WorkspaceBootstrapProgress(
                phase=WorkspaceBootstrapPhase.failed,
                message="Bootstrap failed.",
                failure_message=str(exc),
            ),
        )


async def _poll_until_done(job_id: str, timeout: int = 600) -> dict:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        result = await kennel_client.poll_job(job_id)
        if result["status"] in {"done", "failed"}:
            return result
        await asyncio.sleep(3)
    return {"status": "failed", "error": "provision timeout"}


async def _update_workspace(
    ws_id: uuid.UUID,
    *,
    status: WorkspaceStatus | None = None,
    kennel_job: str | None = None,
    ws_token: str | None = None,
    failure_message: str | None = None,
    bootstrap_progress: WorkspaceBootstrapProgress | None = None,
    meta_updates: dict | None = None,
) -> None:
    async with async_session_maker() as session:
        workspace = await session.get(Workspace, ws_id)
        if workspace is None:
            return

        if status is not None:
            workspace.status = status
            workspace.last_transition_at = datetime.utcnow()
            if status == WorkspaceStatus.requested:
                workspace.requested_at = workspace.requested_at or workspace.last_transition_at
            elif status == WorkspaceStatus.starting:
                workspace.started_at = workspace.last_transition_at
            elif status == WorkspaceStatus.ready:
                workspace.ready_at = workspace.last_transition_at
            elif status == WorkspaceStatus.stopped:
                workspace.stopped_at = workspace.last_transition_at
            elif status == WorkspaceStatus.destroyed:
                workspace.destroyed_at = workspace.last_transition_at
        if kennel_job is not None:
            workspace.kennel_job = kennel_job
        if ws_token is not None:
            workspace.ws_token = ws_token
        if failure_message is not None:
            workspace.failure_message = failure_message

        merged_meta = dict(workspace.meta or {})
        if bootstrap_progress is not None:
            merged_meta["bootstrap_progress"] = bootstrap_progress.model_dump(mode="json")
        if meta_updates:
            merged_meta.update(meta_updates)
        if merged_meta:
            workspace.meta = merged_meta

        workspace.updated_at = datetime.utcnow()
        session.add(workspace)
        await session.commit()


def get_lifecycle_allowed_actions(workspace: Workspace) -> list[WorkspaceAction]:
    if workspace.status in {
        WorkspaceStatus.requested,
        WorkspaceStatus.provisioning,
        WorkspaceStatus.starting,
        WorkspaceStatus.failed,
    }:
        return [WorkspaceAction.destroy]

    if workspace.status == WorkspaceStatus.ready:
        return [
            WorkspaceAction.stop,
            WorkspaceAction.destroy,
            WorkspaceAction.request_terminal,
            WorkspaceAction.discover_services,
        ]

    if workspace.status == WorkspaceStatus.stopped:
        return [WorkspaceAction.start, WorkspaceAction.destroy]

    return []


async def get_allowed_actions_for_user(
    db: AsyncSession,
    *,
    workspace: Workspace,
    user: User,
) -> list[WorkspaceAction]:
    lifecycle_actions = get_lifecycle_allowed_actions(workspace)
    if not lifecycle_actions:
        return []

    if user.is_superuser or workspace.owner_id == user.id:
        return lifecycle_actions

    role = await get_effective_role(
        db,
        user=user,
        resource_type="workspace",
        resource_id=workspace.id,
    )
    if role is None:
        return []

    use_actions = {
        WorkspaceAction.request_terminal,
        WorkspaceAction.discover_services,
    }
    return [action for action in lifecycle_actions if action in use_actions]


def get_terminal_status(workspace: Workspace) -> WorkspaceTerminalStatus:
    if WorkspaceAction.request_terminal not in get_lifecycle_allowed_actions(workspace):
        return WorkspaceTerminalStatus.unavailable
    if workspace.ws_token:
        return WorkspaceTerminalStatus.expired
    return WorkspaceTerminalStatus.available


def bootstrap_kind_from_intent(_bootstrap_intent: WorkspaceBootstrapIntent) -> str | None:
    """
    Placeholder hook for future bootstrap-driven kind selection.

    The current slice keeps `kind` as a top-level workspace concept. This helper
    exists so that future iterations can route flavor/kind decisions through the
    bootstrap plan deliberately rather than scattering that logic through the
    provisioning flow.
    """

    return None


def bootstrap_flavour_from_intent(_bootstrap_intent: WorkspaceBootstrapIntent) -> str | None:
    """See `bootstrap_kind_from_intent()` for the reasoning behind this hook."""

    return None


def is_supported_external_repo_reference(repo_url: str) -> bool:
    """
    Validate external repo references conservatively without closing future doors.

    This accepts:
    - standard URL-shaped git references (`https`, `http`, `ssh`, `git`)
    - common scp-style git references such as `git@github.com:org/repo.git`

    The goal is to reject obviously malformed input while staying permissive
    enough for operator experimentation during this early slice.
    """

    candidate = repo_url.strip()
    if not candidate:
        return False
    if "://" in candidate:
        parsed = urlparse(candidate)
        return bool(parsed.scheme and parsed.netloc)
    return "@" in candidate and ":" in candidate


async def normalize_bootstrap_intent(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID,
    req: WorkspaceCreate,
) -> NormalizedWorkspaceBootstrap:
    """
    Normalize legacy and typed bootstrap input into a single backend-owned shape.

    This is intentionally an early slice:
    - `external_url` is supported directly
    - `user_repo` is validated and currently materializes via the repo's
      `source_repo_url` as a bridge to the richer platform-native repo execution
      path planned in later Track 2 work
    - `shadow_repo` is recognized by the contract but held for a later execution
      slice so we do not over-commit before its materialization semantics are clear
    """

    bootstrap = req.bootstrap or WorkspaceBootstrapIntent()
    repo_source = bootstrap.repo_source

    if repo_source is None and req.repo_url:
        repo_source = WorkspaceExternalUrlRepoSource(repo_url=req.repo_url)

    env_vars = bootstrap.env_vars or req.env_vars
    ssh_pubkey = bootstrap.ssh_pubkey or req.ssh_pubkey
    install_intent = bootstrap.install_intent or WorkspaceInstallIntentNone()
    startup_intent = bootstrap.startup_intent or WorkspaceStartupIntentTerminalOnly()

    normalized_intent = WorkspaceBootstrapIntent(
        repo_source=repo_source,
        workspace_path=bootstrap.workspace_path,
        install_intent=install_intent,
        startup_intent=startup_intent,
        env_vars=env_vars,
        ssh_pubkey=ssh_pubkey,
    )

    materialized_repo_url: str | None = None

    if isinstance(repo_source, WorkspaceExternalUrlRepoSource):
        if not is_supported_external_repo_reference(repo_source.repo_url):
            raise WorkspaceBootstrapValidationError(
                "External repository reference is not valid.",
                error_code="WORKSPACE_EXTERNAL_REPO_INVALID",
            )
        materialized_repo_url = repo_source.repo_url

    elif isinstance(repo_source, WorkspaceUserRepoSource):
        repo = await db.get(UserRepo, repo_source.repo_id)
        if repo is None or repo.owner_user_id != owner_id:
            raise WorkspaceBootstrapValidationError(
                "User repo not found.",
                status_code=404,
                error_code="WORKSPACE_USER_REPO_NOT_FOUND",
            )
        if repo.import_status != UserRepoImportStatus.READY:
            raise WorkspaceBootstrapValidationError(
                "User repo is not ready for workspace bootstrap.",
                status_code=409,
                error_code="WORKSPACE_USER_REPO_NOT_READY",
            )
        materialized_repo_url = repo.source_repo_url

    elif isinstance(repo_source, WorkspaceShadowRepoSource):
        raise WorkspaceBootstrapValidationError(
            "Shadow repo bootstrap is not enabled in this implementation slice yet.",
            status_code=400,
            error_code="WORKSPACE_SHADOW_REPO_UNAVAILABLE",
        )

    bootstrap_plan = generate_bootstrap_plan(
        normalized_intent,
        materialized_repo_url=materialized_repo_url,
    )

    return NormalizedWorkspaceBootstrap(
        intent=normalized_intent,
        materialized_repo_url=materialized_repo_url,
        plan=bootstrap_plan,
    )


async def get_workspace_project_summary(
    db: AsyncSession,
    workspace_id: uuid.UUID,
) -> WorkspaceProjectSummary | None:
    stmt = (
        select(Project)
        .join(ProjectResource, ProjectResource.project_id == Project.id)
        .where(
            ProjectResource.resource_type == "workspace",
            ProjectResource.resource_id == workspace_id,
        )
        .order_by(Project.created_at.desc())
    )
    project = (await db.exec(stmt)).first()
    if project is None:
        return None
    return WorkspaceProjectSummary(id=project.id, name=project.name)


async def user_can_view_workspace(
    db: AsyncSession,
    *,
    workspace: Workspace,
    user: User,
) -> bool:
    if user.is_superuser or workspace.owner_id == user.id:
        return True

    return await has_access(
        db,
        user=user,
        resource_type="workspace",
        resource_id=workspace.id,
        minimum_role=AccessGrantRole.viewer,
    )


async def get_workspace_for_user(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    user: User,
) -> Workspace | None:
    workspace = await db.get(Workspace, workspace_id)
    if workspace is None:
        return None

    if await user_can_view_workspace(db, workspace=workspace, user=user):
        return workspace

    return None


async def list_workspaces_visible_to_user(
    db: AsyncSession,
    *,
    user: User,
    include_destroyed: bool = False,
) -> list[Workspace]:
    stmt = select(Workspace).order_by(Workspace.created_at.desc())
    workspaces = list((await db.exec(stmt)).all())

    visible: list[Workspace] = []
    for workspace in workspaces:
        if not include_destroyed and workspace.status == WorkspaceStatus.destroyed:
            continue
        if await user_can_view_workspace(db, workspace=workspace, user=user):
            visible.append(workspace)

    return visible


def _service_kind_from_value(value: str | None) -> WorkspaceServiceKind:
    try:
        return WorkspaceServiceKind(value) if value is not None else WorkspaceServiceKind.custom
    except ValueError:
        return WorkspaceServiceKind.custom


def _service_status_from_value(value: str | None) -> WorkspaceServiceStatus:
    try:
        return WorkspaceServiceStatus(value) if value is not None else WorkspaceServiceStatus.unknown
    except ValueError:
        return WorkspaceServiceStatus.unknown


def _service_protocol_from_value(value: str | None) -> WorkspaceServiceProtocol:
    try:
        return WorkspaceServiceProtocol(value) if value is not None else WorkspaceServiceProtocol.http
    except ValueError:
        return WorkspaceServiceProtocol.http


def _service_source_from_value(value: str | None) -> WorkspaceServiceSource:
    try:
        return WorkspaceServiceSource(value) if value is not None else WorkspaceServiceSource.bootstrap_profile
    except ValueError:
        return WorkspaceServiceSource.bootstrap_profile


def _service_summary_from_dict(data: dict) -> WorkspaceServiceSummary | None:
    service_id = data.get("id")
    label = data.get("label")
    if not isinstance(service_id, str) or not isinstance(label, str):
        return None

    host = data.get("host")
    port = data.get("port")
    path = data.get("path")
    url = data.get("url")
    readiness_message = data.get("readiness_message")

    return WorkspaceServiceSummary(
        id=service_id,
        kind=_service_kind_from_value(data.get("kind")),
        label=label,
        status=_service_status_from_value(data.get("status")),
        protocol=_service_protocol_from_value(data.get("protocol")),
        host=host if isinstance(host, str) else None,
        port=port if isinstance(port, int) else None,
        path=path if isinstance(path, str) else None,
        url=url if isinstance(url, str) else None,
        source=_service_source_from_value(data.get("source")),
        readiness_message=readiness_message if isinstance(readiness_message, str) else None,
    )


def _fallback_service_summaries(workspace: Workspace) -> list[WorkspaceServiceSummary]:
    meta = workspace.meta or {}
    declared_services = meta.get("declared_services")
    if not isinstance(declared_services, list):
        return []

    services: list[WorkspaceServiceSummary] = []
    for item in declared_services:
        if not isinstance(item, dict):
            continue
        service_id = item.get("id")
        label = item.get("label")
        if not isinstance(service_id, str) or not isinstance(label, str):
            continue

        service_kind = _service_kind_from_value(item.get("kind"))
        path = item.get("path")
        port = item.get("port")
        is_runtime_active = workspace.status in {WorkspaceStatus.starting, WorkspaceStatus.ready}

        if service_kind == WorkspaceServiceKind.agent_runtime:
            fallback_status = (
                WorkspaceServiceStatus.pending
                if workspace.status == WorkspaceStatus.starting
                else WorkspaceServiceStatus.unknown
            )
            fallback_message = (
                "Agent runtime startup has begun, but live discovery has not returned process state yet."
                if workspace.status == WorkspaceStatus.starting
                else "Agent runtime was declared, but live discovery is currently unavailable."
            )
        else:
            fallback_status = (
                WorkspaceServiceStatus.pending
                if is_runtime_active
                else WorkspaceServiceStatus.unknown
            )
            fallback_message = (
                "Service discovery has not returned runtime state yet."
                if is_runtime_active
                else "Runtime service state is unavailable."
            )

        services.append(
            WorkspaceServiceSummary(
                id=service_id,
                kind=service_kind,
                label=label,
                status=fallback_status,
                protocol=_service_protocol_from_value(item.get("protocol")),
                host="127.0.0.1" if isinstance(port, int) else None,
                port=port if isinstance(port, int) else None,
                path=path if isinstance(path, str) else None,
                url=(
                    f"{item.get('protocol', 'http')}://127.0.0.1:{port}{path if isinstance(path, str) else '/'}"
                    if isinstance(port, int)
                    else None
                ),
                source=_service_source_from_value(item.get("source")),
                readiness_message=fallback_message,
            )
        )

    return services


def _services_ready_for_workspace(services: list[WorkspaceServiceSummary]) -> bool:
    agent_runtime_services = [
        service for service in services if service.kind == WorkspaceServiceKind.agent_runtime
    ]
    if agent_runtime_services:
        return any(service.status == WorkspaceServiceStatus.ready for service in agent_runtime_services)
    return any(service.status == WorkspaceServiceStatus.ready for service in services)


async def get_workspace_service_summaries(workspace: Workspace) -> list[WorkspaceServiceSummary]:
    if not workspace.kennel_name:
        return []

    if workspace.status == WorkspaceStatus.stopped:
        return _fallback_service_summaries(workspace)

    if workspace.status not in {WorkspaceStatus.ready, WorkspaceStatus.starting}:
        return []

    try:
        result = await kennel_client.get_env_services(workspace.kennel_name)
    except httpx.HTTPError:
        log.debug("[workspace:%s] kennel service discovery unavailable", workspace.id, exc_info=True)
        return _fallback_service_summaries(workspace)

    services_payload = result.get("services")
    if not isinstance(services_payload, list):
        return _fallback_service_summaries(workspace)

    services: list[WorkspaceServiceSummary] = []
    for item in services_payload:
        if not isinstance(item, dict):
            continue
        service = _service_summary_from_dict(item)
        if service is not None:
            services.append(service)

    return services or _fallback_service_summaries(workspace)


async def get_flavour_health_snapshot(flavour: str) -> FlavourHealthSnapshot | None:
    global _flavour_cache

    now = time.monotonic()
    if _flavour_cache is None or now - _flavour_cache[0] > _FLAVOUR_CACHE_TTL_SECONDS:
        try:
            flavour_payload = await kennel_client.list_flavours()
            if isinstance(flavour_payload, dict):
                _flavour_cache = (now, flavour_payload)
        except httpx.HTTPError:
            log.debug("kennel flavour listing unavailable", exc_info=True)
            return None

    if _flavour_cache is None:
        return None

    flavour_data = _flavour_cache[1].get(flavour)
    if not isinstance(flavour_data, dict):
        return None

    latest_status = flavour_data.get("latest_status")
    latest_job_id = flavour_data.get("latest_job")

    return FlavourHealthSnapshot(
        snapshot_ready=flavour_data.get("snapshot_ready") is True,
        latest_rebuild_status=latest_status if isinstance(latest_status, str) else None,
        latest_rebuild_job_id=latest_job_id if isinstance(latest_job_id, str) else None,
    )


async def to_workspace_public(
    db: AsyncSession,
    workspace: Workspace,
    *,
    user: User | None = None,
) -> WorkspacePublic:
    project_summary = await get_workspace_project_summary(db, workspace.id)
    services = await get_workspace_service_summaries(workspace)
    ready_service_count = sum(1 for service in services if service.status == WorkspaceServiceStatus.ready)
    services_ready = _services_ready_for_workspace(services)
    flavour_health = await get_flavour_health_snapshot(workspace.flavour.value)
    bootstrap_intent = None
    bootstrap_progress = None
    if workspace.meta:
        bootstrap_intent_data = workspace.meta.get("bootstrap_intent")
        if isinstance(bootstrap_intent_data, dict):
            bootstrap_intent = WorkspaceBootstrapIntent.model_validate(bootstrap_intent_data)
        bootstrap_progress_data = workspace.meta.get("bootstrap_progress")
        if isinstance(bootstrap_progress_data, dict):
            bootstrap_progress = WorkspaceBootstrapProgress.model_validate(bootstrap_progress_data)
    allowed_actions = (
        await get_allowed_actions_for_user(db, workspace=workspace, user=user)
        if user is not None
        else get_lifecycle_allowed_actions(workspace)
    )
    return WorkspacePublic.model_validate(
        workspace,
        update={
            "bootstrap": WorkspaceBootstrapState(
                intent=bootstrap_intent,
                progress=bootstrap_progress,
            ) if bootstrap_intent is not None or bootstrap_progress is not None else None,
            "readiness_summary": WorkspaceReadinessSummary(
                terminal_ready=get_terminal_status(workspace) == WorkspaceTerminalStatus.available,
                bootstrap_complete=(
                    bootstrap_progress.phase == WorkspaceBootstrapPhase.complete
                    if bootstrap_progress is not None
                    else False
                ),
                services_ready=services_ready,
                service_count=len(services),
                ready_service_count=ready_service_count,
            ),
            "connectivity_summary": WorkspaceConnectivitySummary(
                terminal_ready=get_terminal_status(workspace) == WorkspaceTerminalStatus.available,
                bootstrap_complete=(
                    bootstrap_progress.phase == WorkspaceBootstrapPhase.complete
                    if bootstrap_progress is not None
                    else False
                ),
                services_ready=services_ready,
                service_count=len(services),
                ready_service_count=ready_service_count,
            ),
            "services": services,
            "flavour_health": WorkspaceFlavourHealthSummary(
                flavour=workspace.flavour.value,
                snapshot_ready=flavour_health.snapshot_ready,
                latest_rebuild_status=flavour_health.latest_rebuild_status,
                latest_rebuild_job_id=flavour_health.latest_rebuild_job_id,
            ) if flavour_health is not None else None,
            "allowed_actions": allowed_actions,
            "visibility": (
                WorkspaceVisibility.project
                if project_summary is not None
                else WorkspaceVisibility.private
            ),
            "project_id": project_summary.id if project_summary is not None else None,
            "project_summary": project_summary,
            "terminal_status": get_terminal_status(workspace),
        },
    )


async def get_terminal_url(
    db: AsyncSession,
    ws_id: uuid.UUID,
    user: User,
) -> str:
    """
    Return the terminal websocket URL for a visible workspace the user may use.
    """
    workspace = await get_workspace_for_user(
        db,
        workspace_id=ws_id,
        user=user,
    )
    if workspace is None:
        raise ValueError("Workspace not found")
    lifecycle_actions = get_lifecycle_allowed_actions(workspace)
    if WorkspaceAction.request_terminal not in lifecycle_actions:
        raise ValueError(f"Workspace not ready: {workspace.status}")
    allowed_actions = await get_allowed_actions_for_user(
        db,
        workspace=workspace,
        user=user,
    )
    if WorkspaceAction.request_terminal not in allowed_actions:
        raise PermissionError("Workspace terminal is not allowed")
    if not workspace.kennel_name:
        raise ValueError("Workspace terminal is not available")

    token_result = await kennel_client.issue_terminal_token(workspace.kennel_name)
    token = token_result.get("token")
    if not token:
        raise ValueError("Workspace terminal is not available")

    workspace.ws_token = token
    workspace.failure_message = None
    workspace.updated_at = datetime.utcnow()
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    return kennel_client.terminal_url(workspace.kennel_name, token)


async def stop_workspace(db: AsyncSession, ws_id: uuid.UUID) -> None:
    workspace = await db.get(Workspace, ws_id)
    if workspace is None or not workspace.kennel_name:
        return

    transition_time = datetime.utcnow()
    workspace.status = WorkspaceStatus.stopping
    workspace.last_transition_at = transition_time
    workspace.failure_message = None
    workspace.updated_at = transition_time
    db.add(workspace)
    await db.flush()

    try:
        await kennel_client.stop_env(workspace.kennel_name)
    except Exception as exc:
        workspace.status = WorkspaceStatus.failed
        workspace.last_transition_at = datetime.utcnow()
        workspace.failure_message = str(exc)
        workspace.updated_at = workspace.last_transition_at
        db.add(workspace)
        await db.flush()
        raise

    workspace.status = WorkspaceStatus.stopped
    workspace.last_transition_at = datetime.utcnow()
    workspace.stopped_at = workspace.last_transition_at
    workspace.updated_at = workspace.last_transition_at
    db.add(workspace)
    await db.flush()


async def start_workspace(db: AsyncSession, ws_id: uuid.UUID) -> None:
    workspace = await db.get(Workspace, ws_id)
    if workspace is None or not workspace.kennel_name:
        return
    if workspace.status != WorkspaceStatus.stopped:
        raise ValueError(f"Workspace cannot be started from {workspace.status}")

    transition_time = datetime.utcnow()
    workspace.status = WorkspaceStatus.starting
    workspace.last_transition_at = transition_time
    workspace.started_at = transition_time
    workspace.failure_message = None
    workspace.updated_at = transition_time
    db.add(workspace)
    await db.flush()

    try:
        response = await kennel_client.get_client().post(
            f"/envs/{workspace.kennel_name}/action",
            json={"action": "restart"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        workspace.status = WorkspaceStatus.failed
        workspace.last_transition_at = datetime.utcnow()
        workspace.failure_message = str(exc)
        workspace.updated_at = workspace.last_transition_at
        db.add(workspace)
        await db.flush()
        raise

    workspace.status = WorkspaceStatus.ready
    workspace.last_transition_at = datetime.utcnow()
    workspace.ready_at = workspace.last_transition_at
    workspace.failure_message = None
    workspace.updated_at = workspace.last_transition_at
    db.add(workspace)
    await db.flush()


async def destroy_workspace(db: AsyncSession, ws_id: uuid.UUID) -> None:
    workspace = await db.get(Workspace, ws_id)
    if workspace is None:
        return

    transition_time = datetime.utcnow()
    workspace.status = WorkspaceStatus.destroying
    workspace.last_transition_at = transition_time
    workspace.failure_message = None
    workspace.updated_at = transition_time
    db.add(workspace)
    await db.flush()

    try:
        if workspace.kennel_name:
            await kennel_client.destroy_env(workspace.kennel_name)
    except Exception as exc:
        workspace.status = WorkspaceStatus.failed
        workspace.last_transition_at = datetime.utcnow()
        workspace.failure_message = str(exc)
        workspace.updated_at = workspace.last_transition_at
        db.add(workspace)
        await db.flush()
        raise

    workspace.status = WorkspaceStatus.destroyed
    workspace.last_transition_at = datetime.utcnow()
    workspace.destroyed_at = workspace.last_transition_at
    workspace.updated_at = workspace.last_transition_at
    db.add(workspace)
    await db.flush()
