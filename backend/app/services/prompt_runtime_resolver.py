from __future__ import annotations

import logging
import uuid
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    PromptConfig,
    PromptConfigDraft,
    PromptConfigVersion,
    RoomAgentSettings,
    UserAgentConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class ResolvedPromptRuntimeConfig:
    payload: dict[str, Any]
    provenance: dict[str, str]


@dataclass
class PromptRuntimePatch:
    payload: dict[str, Any]
    provenance: dict[str, str]


def _messages_to_instructions(messages: list[dict[str, Any]]) -> str | None:
    lines: list[str] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            continue
        role_clean = role.strip().lower() or "user"
        content_clean = content.strip()
        if not content_clean:
            continue
        lines.append(f"[{role_clean}] {content_clean}")
    if not lines:
        return None
    return "\n".join(lines)


def _prompt_draft_to_runtime_patch(prompt: PromptConfigDraft) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    model_id = prompt.model.model_id
    model_name = prompt.model.model_name
    if model_name:
        patch["model_name"] = model_name
    if model_id:
        patch["model"] = model_id

    provider_id = prompt.provider.user_access_provider_id
    if provider_id is not None:
        patch["user_access_provider"] = provider_id

    tool_config: dict[str, Any] = {}
    if prompt.tools is not None:
        tool_mode = prompt.tools.tool_mode or "none"
        tool_config["enable_tools"] = tool_mode in {"optional", "required"}
        tool_config["require_tools"] = tool_mode == "required"
        tool_config["allowed_tools"] = prompt.tools.tool_allowlist or []
        tool_choice = prompt.tools.tool_choice
        if isinstance(tool_choice, dict):
            if tool_choice.get("type") == "named" and isinstance(tool_choice.get("name"), str):
                tool_config["tool_choice"] = tool_choice["name"]
        elif isinstance(tool_choice, str):
            tool_config["tool_choice"] = tool_choice
        if prompt.tools.max_tool_calls is not None:
            tool_config["max_tool_calls"] = prompt.tools.max_tool_calls
        if prompt.tools.builtin is not None:
            tool_config["builtin"] = prompt.tools.builtin
        if prompt.tools.mcp is not None:
            tool_config["mcp"] = prompt.tools.mcp
        patch["tool_config"] = tool_config

    model_settings: dict[str, Any] = {}
    if prompt.params.temperature is not None:
        model_settings["temperature"] = prompt.params.temperature
    if prompt.params.top_p is not None:
        model_settings["top_p"] = prompt.params.top_p
    if prompt.params.max_output_tokens is not None:
        model_settings["max_tokens"] = prompt.params.max_output_tokens
    if prompt.params.stop is not None:
        model_settings["stop_sequences"] = prompt.params.stop
    if prompt.params.seed is not None:
        model_settings["seed"] = prompt.params.seed
    if prompt.params.parallel_tool_calls is not None:
        model_settings["parallel_tool_calls"] = prompt.params.parallel_tool_calls
    if prompt.params.reasoning_effort is not None:
        model_settings["openai_reasoning_effort"] = prompt.params.reasoning_effort
    if prompt.params.openai is not None:
        previous_response_id = prompt.params.openai.get("previous_response_id")
        if previous_response_id:
            model_settings["openai_previous_response_id"] = previous_response_id
        reasoning = prompt.params.openai.get("reasoning")
        if isinstance(reasoning, dict):
            summary = reasoning.get("summary")
            if summary in {"concise", "detailed"}:
                model_settings["openai_reasoning_summary"] = summary
    if model_settings:
        patch["model_settings"] = model_settings

    if prompt.input.kind == "simple_text":
        if prompt.input.text.strip():
            patch["instructions"] = prompt.input.text.strip()
    else:
        if prompt.input.system and prompt.input.system.strip():
            patch["custom_system_prompt"] = prompt.input.system.strip()
        instructions = _messages_to_instructions(
            [message.model_dump(mode="json") for message in prompt.input.messages]
        )
        if instructions:
            patch["instructions"] = instructions

    return patch


def _runtime_patch_from_prompt(
    *,
    prompt: PromptConfigDraft,
    source: str,
) -> PromptRuntimePatch:
    payload = _prompt_draft_to_runtime_patch(prompt)
    return PromptRuntimePatch(
        payload=payload,
        provenance={key: source for key in payload.keys()},
    )


def _merge_runtime_patches(*patches: PromptRuntimePatch | None) -> PromptRuntimePatch | None:
    merged_payload: dict[str, Any] = {}
    merged_provenance: dict[str, str] = {}
    for patch in patches:
        if patch is None:
            continue
        for key, value in patch.payload.items():
            merged_payload[key] = value
            merged_provenance[key] = patch.provenance.get(key, "unknown")
    if not merged_payload:
        return None
    return PromptRuntimePatch(payload=merged_payload, provenance=merged_provenance)


def _room_prompt_json_to_draft(prompt_json: dict[str, Any]) -> PromptConfigDraft | None:
    try:
        return PromptConfigDraft.model_validate(prompt_json)
    except Exception:
        logger.warning("Ignoring invalid room prompt_config payload", exc_info=True)
        return None


def _agent_base_payload(config: UserAgentConfig) -> dict[str, Any]:
    return {
        "model": config.model,
        "model_name": config.model_name or config.model,
        "system_prompt": config.system_prompt,
        "custom_system_prompt": config.custom_system_prompt,
        "instructions": config.instructions,
        "user_access_provider": config.user_access_provider,
        "provider_type": config.provider_type,
        "tool_config": deepcopy(config.tool_config) if config.tool_config else None,
        "deps_config": deepcopy(config.deps_config) if config.deps_config else None,
        "model_settings": None,
        "max_tool_iterations": config.max_tool_iterations,
    }


def _apply_patch(
    *,
    payload: dict[str, Any],
    provenance: dict[str, str],
    patch: dict[str, Any],
    source: str | dict[str, str],
) -> None:
    for key, value in patch.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        payload[key] = value
        if isinstance(source, dict):
            provenance[key] = source.get(key, "unknown")
        else:
            provenance[key] = source


def resolve_effective_prompt_runtime_config(
    *,
    agent_config: UserAgentConfig,
    bound_prompt: PromptConfigDraft | None = None,
    room_defaults_prompt: PromptConfigDraft | None = None,
    room_agent_prompt: PromptConfigDraft | None = None,
    room_defaults_patch: PromptRuntimePatch | None = None,
    room_agent_patch: PromptRuntimePatch | None = None,
) -> ResolvedPromptRuntimeConfig:
    payload = _agent_base_payload(agent_config)
    provenance = {key: "user_agent_config" for key in payload.keys()}

    if bound_prompt is not None:
        _apply_patch(
            payload=payload,
            provenance=provenance,
            patch=_prompt_draft_to_runtime_patch(bound_prompt),
            source="bound_prompt_config",
        )
    if room_defaults_patch is None and room_defaults_prompt is not None:
        room_defaults_patch = _runtime_patch_from_prompt(
            prompt=room_defaults_prompt,
            source="room_defaults_override",
        )
    if room_defaults_patch is not None:
        _apply_patch(
            payload=payload,
            provenance=provenance,
            patch=room_defaults_patch.payload,
            source=room_defaults_patch.provenance,
        )
    if room_agent_patch is None and room_agent_prompt is not None:
        room_agent_patch = _runtime_patch_from_prompt(
            prompt=room_agent_prompt,
            source="room_agent_override",
        )
    if room_agent_patch is not None:
        _apply_patch(
            payload=payload,
            provenance=provenance,
            patch=room_agent_patch.payload,
            source=room_agent_patch.provenance,
        )

    return ResolvedPromptRuntimeConfig(payload=payload, provenance=provenance)


async def resolve_effective_prompt_runtime_config_for_room(
    *,
    session: AsyncSession,
    agent_config: UserAgentConfig,
    room_id: uuid.UUID | None,
    bound_prompt: PromptConfigDraft | None = None,
) -> ResolvedPromptRuntimeConfig:
    bound_prompt_resolved = bound_prompt
    if bound_prompt_resolved is None:
        bound_prompt_resolved = await _resolve_bound_prompt_for_agent(
            session=session,
            agent_config=agent_config,
        )

    room_defaults_prompt: PromptConfigDraft | None = None
    room_agent_prompt: PromptConfigDraft | None = None

    if room_id is not None:
        stmt = select(RoomAgentSettings).where(RoomAgentSettings.room_id == room_id)
        rows = list((await session.exec(stmt)).all())
        room_defaults = next((row for row in rows if row.agent_slug is None), None)
        room_agent = next(
            (
                row
                for row in rows
                if row.agent_slug is not None and row.agent_slug == agent_config.slug
            ),
            None,
        )
        room_defaults_patch = await _resolve_room_settings_prompt_patch(
            session=session,
            room_settings=room_defaults,
            owner_id=getattr(agent_config, "owner_id", None),
            source_prefix="room_defaults",
        )
        room_agent_patch = await _resolve_room_settings_prompt_patch(
            session=session,
            room_settings=room_agent,
            owner_id=getattr(agent_config, "owner_id", None),
            source_prefix="room_agent",
        )
    else:
        room_defaults_patch = None
        room_agent_patch = None

    return resolve_effective_prompt_runtime_config(
        agent_config=agent_config,
        bound_prompt=bound_prompt_resolved,
        room_defaults_prompt=room_defaults_prompt,
        room_agent_prompt=room_agent_prompt,
        room_defaults_patch=room_defaults_patch,
        room_agent_patch=room_agent_patch,
    )


async def _resolve_bound_prompt_for_agent(
    *,
    session: AsyncSession,
    agent_config: UserAgentConfig,
) -> PromptConfigDraft | None:
    return await _resolve_prompt_config_reference(
        session=session,
        prompt_config_id=getattr(agent_config, "prompt_config_id", None),
        owner_id=getattr(agent_config, "owner_id", None),
        policy=getattr(agent_config, "prompt_config_version_policy", None),
        requested_version=getattr(agent_config, "prompt_config_version_number", None),
        binding_label=f"agent {getattr(agent_config, 'slug', '<unknown>')}",
    )


async def _resolve_room_settings_prompt_patch(
    *,
    session: AsyncSession,
    room_settings: RoomAgentSettings | None,
    owner_id: uuid.UUID | None,
    source_prefix: str,
) -> PromptRuntimePatch | None:
    """
    Resolve a room-scoped prompt layer into a runtime patch.

    Ordering within a single room layer is intentional and stable:
    1. referenced PromptConfig version, if attached
    2. inline `prompt_config` overlay payload, if present

    This keeps room/session attach inspectable and extensible for future UI surfaces
    without introducing a separate merge model outside the shared runtime resolver.
    """
    if room_settings is None:
        return None

    referenced_prompt = await _resolve_prompt_config_reference(
        session=session,
        prompt_config_id=getattr(room_settings, "prompt_config_id", None),
        owner_id=owner_id,
        policy=getattr(room_settings, "prompt_config_version_policy", None),
        requested_version=getattr(room_settings, "prompt_config_version_number", None),
        binding_label=f"{source_prefix} room settings",
    )
    inline_prompt = None
    if isinstance(room_settings.prompt_config, dict):
        inline_prompt = _room_prompt_json_to_draft(room_settings.prompt_config)

    return _merge_runtime_patches(
        _runtime_patch_from_prompt(
            prompt=referenced_prompt,
            source=f"{source_prefix}_prompt_config",
        )
        if referenced_prompt is not None
        else None,
        _runtime_patch_from_prompt(
            prompt=inline_prompt,
            source=f"{source_prefix}_inline_override",
        )
        if inline_prompt is not None
        else None,
    )


async def _resolve_prompt_config_reference(
    *,
    session: AsyncSession,
    prompt_config_id: uuid.UUID | None,
    owner_id: uuid.UUID | None,
    policy: str | None,
    requested_version: int | None,
    binding_label: str,
) -> PromptConfigDraft | None:
    """Resolve a persisted PromptConfig reference to a concrete PromptConfigDraft payload."""
    if prompt_config_id is None:
        return None

    prompt_config = await session.get(PromptConfig, prompt_config_id)
    if prompt_config is None:
        logger.warning(
            "%s references missing prompt_config_id=%s",
            binding_label,
            prompt_config_id,
        )
        return None
    if (
        prompt_config.owner_id is not None
        and owner_id is not None
        and prompt_config.owner_id != owner_id
    ):
        logger.warning(
            "%s prompt_config ownership mismatch (owner=%s prompt_owner=%s)",
            binding_label,
            owner_id,
            prompt_config.owner_id,
        )
        return None

    target_version: int | None = None
    if policy == "pinned" and isinstance(requested_version, int) and requested_version > 0:
        target_version = requested_version
    else:
        target_version = prompt_config.latest_version

    version_row = None
    if target_version is not None:
        version_row = (
            await session.exec(
                select(PromptConfigVersion).where(
                    PromptConfigVersion.prompt_config_id == prompt_config_id,
                    PromptConfigVersion.version_number == target_version,
                )
            )
        ).first()
    if version_row is None and prompt_config.latest_version is not None:
        version_row = (
            await session.exec(
                select(PromptConfigVersion).where(
                    PromptConfigVersion.prompt_config_id == prompt_config_id,
                    PromptConfigVersion.version_number == prompt_config.latest_version,
                )
            )
        ).first()
    if version_row is None:
        logger.warning(
            "No prompt version found for %s prompt_config_id=%s (policy=%s target=%s)",
            binding_label,
            prompt_config_id,
            policy,
            target_version,
        )
        return None
    try:
        return PromptConfigDraft.model_validate(version_row.payload_json)
    except Exception:
        logger.warning(
            "Invalid prompt payload for %s prompt_config_id=%s version=%s",
            binding_label,
            prompt_config_id,
            version_row.version_number,
            exc_info=True,
        )
        return None
