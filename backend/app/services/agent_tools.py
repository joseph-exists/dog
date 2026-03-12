from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel
from pydantic_ai import RunContext
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import engine
from app.models import RoomParticipant, User
from app.schemas.ag_ui import UIComponent, UIComponentType
from app.services.a2a_orchestrator import DEFAULT_MAX_A2A_DEPTH, A2AOrchestrator
from app.services.agent_prompt import build_agent_prompt
from app.services.context_provider import build_room_context
from app.services.context_store import RedisContextStore
from app.services.user_repo_service import (
    UserRepoFileMutation,
    UserRepoWriteConflict,
    UserRepoWriteFailed,
    UserRepoWriteNotFound,
    UserRepoWriteNotReady,
    UserRepoWriteUnauthorized,
    UserRepoWriteUnsupportedBranch,
    UserRepoWriteValidationError,
    user_repo_service,
)
from app.services.user_repo_view_service import (
    UserRepoBackendUnavailable,
    UserRepoBranchNotFound,
    UserRepoPathError,
    UserRepoViewNotFound,
    user_repo_view_service,
)

logger = logging.getLogger(__name__)

_a2a_orchestrator = A2AOrchestrator(max_depth=DEFAULT_MAX_A2A_DEPTH)


@dataclass
class AgentDeps:
    """
    Dependencies passed to agent tools via PydanticAI's RunContext.

    This enables tools to access:
    - Database session for queries
    - Room context for multi-agent coordination
    - Current agent info for self-awareness
    - UI components collector for AG-UI

    Usage in tools:
        async def my_tool(ctx: RunContext[AgentDeps], arg: str) -> str:
            session = ctx.deps.session
            room_id = ctx.deps.room_id
            ...
    """

    session: AsyncSession
    room_id: uuid.UUID
    current_agent_slug: str
    acting_user_id: uuid.UUID | None = None
    a2a_depth: int = 0
    # AG-UI: Collected UI components (populated by emit_ui_component tool)
    ui_components: list[UIComponent] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.ui_components is None:
            self.ui_components = []

    def add_ui_component(self, component: UIComponent) -> None:
        """Add a UI component to the collection."""
        if self.ui_components is None:
            self.ui_components = []
        self.ui_components.append(component)


async def request_agent_assistance(
    ctx: RunContext[AgentDeps],
    target_agent: str,
    request: str, 
) -> str:
    """
    Request another agent's expertise on a specific topic.

    Use this tool when you need specialized help from another agent in the room.
    The target agent will process your request and return their response.
    """
    deps = ctx.deps

    if deps.a2a_depth >= DEFAULT_MAX_A2A_DEPTH:
        return (
            f"[A2A limit reached] Cannot request assistance from {target_agent} - "
            f"maximum agent chain depth ({DEFAULT_MAX_A2A_DEPTH}) exceeded."
        )

    if target_agent.lower() == deps.current_agent_slug.lower():
        return "[Error] Cannot request assistance from yourself."

    is_in_room, agent_slug, config = await _a2a_orchestrator.is_agent_in_room(
        session=deps.session,
        room_id=deps.room_id,
        agent_identifier=target_agent,
    )

    if not is_in_room or not agent_slug:
        return (
            f"[Agent not found] '{target_agent}' is not available in this room. "
            f"Check the agent name or ask the user to add them to the room."
        )

    logger.info(
        f"A2A Tool: {deps.current_agent_slug} requesting assistance from {agent_slug} "
        f"(depth {deps.a2a_depth} -> {deps.a2a_depth + 1})"
    )

    response = await _run_agent_for_tool_call(
        room_id=deps.room_id,
        agent_slug=agent_slug,
        request=request,
        requesting_agent=deps.current_agent_slug,
        session=deps.session,
        _a2a_depth=deps.a2a_depth + 1,
    )

    if response["success"]:
        return response["content"]
    else:
        return f"[Error from {agent_slug}] {response.get('error', 'Unknown error')}"


async def _run_agent_for_tool_call(
    *,
    room_id: uuid.UUID,
    agent_slug: str,
    request: str,
    requesting_agent: str,
    session: AsyncSession,
    _a2a_depth: int,
) -> dict[str, Any]:
    """
    Internal function to run an agent for a tool call (non-streaming).

    Unlike run_agent_for_room_streaming, this:
    - Does NOT emit room_message.agent events (response goes back to calling agent)
    - Does NOT publish tokens to Redis
    - Does NOT enable A2A tools on target agent (prevents infinite recursion)
    - Returns response directly to the calling tool
    """
    from app.services.agent_instance import get_agent_instance

    agent = await get_agent_instance(session, agent_slug)
    if not agent:
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": f"Failed to instantiate agent '{agent_slug}'",
        }

    try:
        context = await build_room_context(
            room_id=room_id,
            session=session,
            message_limit=20,
            agent_slug=agent_slug,
            context_store=RedisContextStore(),
        )

        prompt = f"@{requesting_agent} is asking for your assistance:\n\n{request}"
        full_prompt = build_agent_prompt(prompt, context, current_agent_slug=agent_slug)

        result = await agent.run(full_prompt)

        logger.debug(
            f"A2A Tool: {agent_slug} responded to {requesting_agent} "
            f"({len(result.output)} chars)"
        )

        return {
            "agent_name": agent_slug,
            "content": result.output,
            "success": True,
            "error": None,
        }

    except Exception as exc:
        logger.error(f"A2A Tool error: {agent_slug} failed to respond: {exc}")
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": str(exc),
        }


def _write_repo_files_sync(
    *,
    room_id: uuid.UUID,
    acting_user_id: uuid.UUID,
    repo_id: uuid.UUID,
    branch: str,
    commit_message: str,
    mutations: list[dict[str, Any]],
    expected_head_sha: str | None,
) -> str:
    with Session(engine) as sync_session:
        participant = sync_session.exec(
            select(RoomParticipant).where(
                RoomParticipant.room_id == room_id,
                RoomParticipant.participant_type == "user",
                RoomParticipant.participant_id == str(acting_user_id),
                RoomParticipant.active.is_(True),
            )
        ).first()
        if not participant:
            return "Write blocked: acting user is not an active room participant."

        actor = sync_session.get(User, acting_user_id)
        if not actor:
            return "Write blocked: acting user not found."

        if len(mutations) == 0:
            return "Write blocked: at least one mutation is required."
        if len(mutations) > 100:
            return "Write blocked: too many mutations in one request (max 100)."

        parsed_mutations: list[UserRepoFileMutation] = []
        for idx, mutation in enumerate(mutations):
            if not isinstance(mutation, dict):
                return f"Write blocked: mutation at index {idx} must be an object."
            path = str(mutation.get("path") or "").strip()
            operation = str(mutation.get("operation") or "").strip()
            content = mutation.get("content")
            encoding = str(mutation.get("encoding") or "utf-8").strip()
            parsed_mutations.append(
                UserRepoFileMutation(
                    path=path,
                    operation=operation,
                    content=content if content is None or isinstance(content, str) else str(content),
                    encoding=encoding,
                )
            )

        normalized_expected_head_sha = (expected_head_sha or "").strip()
        normalized_branch = (branch or "").strip()
        if not normalized_expected_head_sha:
            # Preserve optimistic concurrency by snapshotting HEAD right before commit.
            user_repo = user_repo_service.authorize_user_repo_write(
                session=sync_session,
                current_user_id=acting_user_id,
                is_superuser=bool(actor.is_superuser),
                repo_id=repo_id,
            )
            normalized_expected_head_sha = user_repo_service._resolve_repo_head_sha(  # noqa: SLF001
                user_repo=user_repo,
                ref=normalized_branch,
            )

        result = user_repo_service.commit_user_repo_changes(
            session=sync_session,
            repo_id=repo_id,
            actor_user_id=acting_user_id,
            branch=normalized_branch,
            mutations=parsed_mutations,
            commit_message=(commit_message or "").strip(),
            expected_head_sha=normalized_expected_head_sha,
            is_superuser=bool(actor.is_superuser),
        )

    changed_paths = ", ".join(result.changed_paths[:10])
    if len(result.changed_paths) > 10:
        changed_paths += ", ..."
    return (
        f"Committed {len(result.changed_paths)} file change(s) to repo {result.repo_id} on branch "
        f"'{result.branch}'. New HEAD: {result.new_head_sha}. Paths: {changed_paths}"
    )


def _read_repo_file_sync(
    *,
    room_id: uuid.UUID,
    acting_user_id: uuid.UUID,
    repo_id: uuid.UUID,
    path: str,
    ref: str | None,
) -> str:
    with Session(engine) as sync_session:
        participant = sync_session.exec(
            select(RoomParticipant).where(
                RoomParticipant.room_id == room_id,
                RoomParticipant.participant_type == "user",
                RoomParticipant.participant_id == str(acting_user_id),
                RoomParticipant.active.is_(True),
            )
        ).first()
        if not participant:
            return "Read blocked: acting user is not an active room participant."

        actor = sync_session.get(User, acting_user_id)
        if not actor:
            return "Read blocked: acting user not found."

        user_repo = user_repo_view_service.authorize_user_repo_read(
            session=sync_session,
            current_user_id=acting_user_id,
            is_superuser=bool(actor.is_superuser),
            repo_id=repo_id,
        )
        file_content = user_repo_view_service.get_file_content(
            session=sync_session,
            repo_id=repo_id,
            path=path,
            ref=ref,
        )

        write_branch = user_repo.source_branch
        if not write_branch:
            return "Read failed: repo default branch is unavailable."
        expected_head_sha = user_repo_service._resolve_repo_head_sha(  # noqa: SLF001
            user_repo=user_repo,
            ref=write_branch,
        )

        payload = {
            "repo_id": str(repo_id),
            "path": file_content.path,
            "resolved_ref": file_content.ref,
            "is_binary": file_content.is_binary,
            "is_truncated": file_content.is_truncated,
            "content_type": file_content.content_type,
            "size_bytes": file_content.size_bytes,
            "encoding": file_content.encoding,
            "content": file_content.content,
            "write_hint": {
                "branch": write_branch,
                "expected_head_sha": expected_head_sha,
            },
        }
        return json.dumps(payload, ensure_ascii=True)


async def write_repo_files(
    ctx: RunContext[AgentDeps],
    repo_id: str,
    branch: str,
    commit_message: str,
    mutations: list[dict[str, Any]],
    expected_head_sha: str | None = None,
) -> str:
    """
    Write files to a user repo and commit the change.

    Mutations must be a list of objects:
    - upsert: {"path":"src/app.py","operation":"upsert","content":"...","encoding":"utf-8"}
    - delete: {"path":"old.txt","operation":"delete"}
    """
    deps = ctx.deps
    if deps.acting_user_id is None:
        return "Write blocked: no acting user context is available for this room agent run."

    try:
        repo_uuid = uuid.UUID(repo_id)
    except ValueError:
        return f"Write blocked: invalid repo_id '{repo_id}'."

    try:
        return await asyncio.to_thread(
            _write_repo_files_sync,
            room_id=deps.room_id,
            acting_user_id=deps.acting_user_id,
            repo_id=repo_uuid,
            branch=branch,
            commit_message=commit_message,
            mutations=mutations,
            expected_head_sha=expected_head_sha,
        )
    except UserRepoWriteNotFound:
        return "Write failed: repo not found."
    except UserRepoWriteUnauthorized:
        return "Write failed: user is not allowed to modify this repo."
    except UserRepoWriteNotReady as exc:
        return f"Write failed: {exc}"
    except UserRepoWriteUnsupportedBranch as exc:
        return f"Write failed: {exc}"
    except UserRepoWriteConflict as exc:
        return f"Write conflict: {exc}. Refresh HEAD and retry."
    except UserRepoWriteValidationError as exc:
        return f"Write validation failed: {exc}"
    except UserRepoWriteFailed as exc:
        return f"Write failed: {exc}"
    except Exception as exc:
        logger.exception(
            "write_repo_files tool error room_id=%s agent=%s repo_id=%s",
            deps.room_id,
            deps.current_agent_slug,
            repo_id,
        )
        return f"Write failed due to unexpected error: {exc}"


async def read_repo_file(
    ctx: RunContext[AgentDeps],
    repo_id: str,
    path: str,
    ref: str | None = None,
) -> str:
    """
    Read one file from a user repo and return JSON payload.

    The JSON includes a write hint:
    - write_hint.branch
    - write_hint.expected_head_sha
    """
    deps = ctx.deps
    if deps.acting_user_id is None:
        return "Read blocked: no acting user context is available for this room agent run."

    normalized_path = (path or "").strip()
    if not normalized_path:
        return "Read blocked: path is required."

    try:
        repo_uuid = uuid.UUID(repo_id)
    except ValueError:
        return f"Read blocked: invalid repo_id '{repo_id}'."

    try:
        return await asyncio.to_thread(
            _read_repo_file_sync,
            room_id=deps.room_id,
            acting_user_id=deps.acting_user_id,
            repo_id=repo_uuid,
            path=normalized_path,
            ref=(ref or "").strip() or None,
        )
    except UserRepoViewNotFound:
        return "Read failed: repo not found."
    except UserRepoBranchNotFound as exc:
        return f"Read failed: {exc}"
    except UserRepoPathError as exc:
        return f"Read failed: {exc}"
    except UserRepoBackendUnavailable as exc:
        return f"Read failed: {exc}"
    except Exception as exc:
        logger.exception(
            "read_repo_file tool error room_id=%s agent=%s repo_id=%s path=%s",
            deps.room_id,
            deps.current_agent_slug,
            repo_id,
            normalized_path,
        )
        return f"Read failed due to unexpected error: {exc}"


def emit_ui_component(
    ctx: RunContext[AgentDeps],
    component_type: UIComponentType,
    data: dict[str, Any],
    fallback_text: str | None = None,
) -> str:
    """
    Emit a structured UI component to be displayed alongside your response.

    The `data` dict MUST match the exact schema for the given `component_type`.
    Use the correct field names below — do NOT invent your own field names.

    ## Component Schemas

    ### card
    - title: str (REQUIRED)
    - body: str (REQUIRED, supports markdown)
    - subtitle: str | null
    - footer: str | null
    - variant: "default" | "highlight" | "warning" | "success" | "info"
    - icon: str | null

    ### list
    - items: list of {label: str, description?: str, icon?: str, badge?: str} (REQUIRED)
    - title: str | null
    - ordered: bool (default false)
    - variant: "default" | "compact" | "detailed"

    ### table
    - columns: list of {key: str, header: str, align?: "left"|"center"|"right"} (REQUIRED)
    - rows: list of dicts mapping column keys to values (REQUIRED)
    - title: str | null
    - striped: bool (default true)
    - compact: bool (default false)

    ### progress
    - items: list of {label: str, value: int (0-100), color?: "blue"|"green"|"yellow"|"red"|"purple"} (REQUIRED)
    - title: str | null
    - show_percentage: bool (default true)

    ### action_buttons
    - buttons: list of {label: str, action: str, variant?: "primary"|"secondary"|"outline"|"ghost", disabled?: bool} (REQUIRED)
    - layout: "horizontal" | "vertical" | "grid" (default "horizontal")
    NOTE: "action" must be a plain STRING identifier (e.g. "expand_details"), NOT an object.
    NOTE: Use "label" for button text, NOT "title" or "text".

    ### code
    - code: str (REQUIRED)
    - language: str | null (e.g. "python", "json")
    - title: str | null
    - line_numbers: bool (default false)

    ### quote
    - text: str (REQUIRED)
    - attribution: str | null
    - variant: "default" | "highlight" | "subtle"

    ### alert
    - message: str (REQUIRED)
    - title: str | null
    - variant: "info" | "success" | "warning" | "error"
    - dismissible: bool (default false)

    ### collapsible
    - title: str (REQUIRED)
    - content: str (REQUIRED, supports markdown)
    - default_open: bool (default false)
    - icon: str | null

    ### tabs
    - tabs: list of {label: str, content: str} (REQUIRED)
    - default_tab: int (default 0)

    ### divider
    - label: str | null
    - variant: "solid" | "dashed" | "dotted"
    """
    # -------------------------------------------------------------------------
    # Validate data against the correct Pydantic schema for this component type.
    # This catches field name mistakes (e.g. "title" vs "label") early and gives
    # the LLM a clear error message it can use to self-correct on retry.
    # -------------------------------------------------------------------------
    from app.schemas.ag_ui import (
        UIActionButtons as UIActionButtonsModel,
    )
    from app.schemas.ag_ui import (
        UIAlert as UIAlertModel,
    )
    from app.schemas.ag_ui import (
        UICard as UICardModel,
    )
    from app.schemas.ag_ui import (
        UICodeBlock as UICodeBlockModel,
    )
    from app.schemas.ag_ui import (
        UICollapsible as UICollapsibleModel,
    )
    from app.schemas.ag_ui import (
        UIDivider as UIDividerModel,
    )
    from app.schemas.ag_ui import (
        UIList as UIListModel,
    )
    from app.schemas.ag_ui import (
        UIPageLayoutPreview as UIPageLayoutPreviewModel,
    )
    from app.schemas.ag_ui import (
        UIProgress as UIProgressModel,
    )
    from app.schemas.ag_ui import (
        UIQuote as UIQuoteModel,
    )
    from app.schemas.ag_ui import (
        UITable as UITableModel,
    )
    from app.schemas.ag_ui import (
        UITabs as UITabsModel,
    )

    _COMPONENT_VALIDATORS: dict[str, type[BaseModel]] = {
        "card": UICardModel,
        "list": UIListModel,
        "table": UITableModel,
        "progress": UIProgressModel,
        "action_buttons": UIActionButtonsModel,
        "code": UICodeBlockModel,
        "quote": UIQuoteModel,
        "alert": UIAlertModel,
        "collapsible": UICollapsibleModel,
        "tabs": UITabsModel,
        "divider": UIDividerModel,
        "page_layout_preview": UIPageLayoutPreviewModel,
    }

    validator = _COMPONENT_VALIDATORS.get(component_type)
    if validator:
        try:
            validated = validator.model_validate(data)
            # Use the validated+normalized data (fills defaults, strips extras)
            data = validated.model_dump()
        except Exception as exc:
            error_msg = (
                f"[UI Component Error: {component_type}] Invalid data: {exc}. "
                f"Please fix the data fields and call emit_ui_component again. "
                f"Refer to the schema in the tool description for correct field names."
            )
            logger.warning(
                f"AG-UI: Agent {ctx.deps.current_agent_slug} emitted invalid "
                f"{component_type} data: {exc}"
            )
            return error_msg

    component = UIComponent(
        type=component_type,
        data=data,
        fallback_text=fallback_text,
    )

    ctx.deps.add_ui_component(component)

    logger.debug(
        f"AG-UI: Agent {ctx.deps.current_agent_slug} emitted {component_type} component"
    )

    return f"[UI Component Added: {component_type}] Component will be displayed with your response."
