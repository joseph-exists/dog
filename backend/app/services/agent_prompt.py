from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

PROMPT_BUILDER_VERSION = "agent_prompt.v1"

_AUDIT_ONLY_CONTEXT_KEYS = {
    "id",
    "entity_id",
    "version_number",
    "commit_sha",
    "source",
    "is_stale",
    "request_id",
    "rendered_at",
    "expires_at",
    "issued_at",
    "url",
    "auth_mode",
}


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _sanitize_prompt_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _sanitize_prompt_payload(item)
            for key, item in value.items()
            if str(key) not in _AUDIT_ONLY_CONTEXT_KEYS
        }
    if isinstance(value, list):
        return [_sanitize_prompt_payload(item) for item in value]
    return value


def _render_shadow_summary_context(
    *,
    context_type: str,
    payload: dict[str, Any],
    current_agent_slug: str | None,
) -> str | None:
    if payload.get("missing_shadow_snapshot") is True:
        return None

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return None

    if context_type == "shadow.agent.summary":
        agent = summary.get("agent")
        if not isinstance(agent, dict):
            return None
        slug = str(agent.get("slug") or "")
        # The current agent's identity already belongs in system_prompt.
        # Keep the full Shadow record in audit storage, but avoid repeating it
        # as provider-facing user context.
        if current_agent_slug and slug == current_agent_slug:
            return None
        name = str(agent.get("name") or slug or "agent")
        description = str(agent.get("description") or "").strip()
        capabilities = agent.get("capabilities")
        capability_text = ""
        if isinstance(capabilities, list) and capabilities:
            capability_text = f" Capabilities: {', '.join(str(c) for c in capabilities)}."
        description_text = f": {description}" if description else ""
        return f"Agent summary - {name}{description_text}.{capability_text}".strip()

    sanitized = _sanitize_prompt_payload(summary)
    if sanitized in ({}, []):
        return None
    return f"{context_type}: {_compact_json(sanitized)}"


def _render_system_context_for_prompt(
    *,
    context_type: str,
    payload: dict[str, Any],
) -> str | None:
    if context_type.startswith("system.canvas."):
        panel_id = payload.get("panel_id")
        return f"Canvas context available for panel {panel_id or 'unknown'}; SVG omitted."

    if context_type == "system.demo.composition":
        panels = payload.get("panels")
        blocks = payload.get("blocks")
        panel_titles = []
        if isinstance(panels, list):
            for panel in panels[:8]:
                if isinstance(panel, dict):
                    title = panel.get("title") or panel.get("kind") or panel.get("id")
                    if title:
                        panel_titles.append(str(title))
        block_titles = []
        if isinstance(blocks, list):
            for block in blocks[:8]:
                if isinstance(block, dict):
                    title = block.get("title") or block.get("type") or block.get("id")
                    if title:
                        block_titles.append(str(title))
        parts = []
        if panel_titles:
            parts.append(f"panels: {', '.join(panel_titles)}")
        if block_titles:
            parts.append(f"blocks: {', '.join(block_titles)}")
        return f"Demo composition ({'; '.join(parts)})" if parts else None

    if context_type == "system.room.workspace_connection.current":
        workspace_name = payload.get("workspace_name") or payload.get("workspace_id")
        state = payload.get("state")
        capabilities = payload.get("capabilities")
        capability_text = ""
        if isinstance(capabilities, list) and capabilities:
            capability_text = f"; capabilities: {', '.join(str(c) for c in capabilities)}"
        return f"Workspace connection: {workspace_name or 'unknown'} ({state or 'unknown'}{capability_text})"

    sanitized = _sanitize_prompt_payload(payload)
    if sanitized in ({}, []):
        return None
    return f"{context_type}: {_compact_json(sanitized)}"


def render_extra_context_for_prompt(
    item: dict[str, Any],
    *,
    current_agent_slug: str | None = None,
) -> str | None:
    context_type = str(item.get("context_type") or "unknown")
    source = str(item.get("source") or "unknown")
    payload = item.get("payload")
    if not isinstance(payload, dict):
        return None if payload in (None, "") else f"{context_type}: {payload}"

    if source == "shadow" or context_type.startswith("shadow."):
        return _render_shadow_summary_context(
            context_type=context_type,
            payload=payload,
            current_agent_slug=current_agent_slug,
        )

    if source == "system" or context_type.startswith("system."):
        return _render_system_context_for_prompt(
            context_type=context_type,
            payload=payload,
        )

    sanitized = _sanitize_prompt_payload(payload)
    if sanitized in ({}, []):
        return None
    return f"{context_type}: {_compact_json(sanitized)}"


def build_agent_prompt(
    trigger_message: str,
    context: Any,
    current_agent_slug: str | None = None,
) -> str:
    """
    Build the full prompt for an agent including room context and other agents.

    Args:
        trigger_message: The user's message that triggered the agent
        context: RoomContext from context_provider
        current_agent_slug: Slug of the agent receiving this prompt (to exclude from list)

    Returns:
        Full prompt string with context prepended
    """
    conversation_context = ""

    # Add story context if available
    if context.story_data:
        conversation_context += f"\nStory: {context.story_data.get('title', 'Untitled')}\n"
        if context.story_data.get("description"):
            conversation_context += (
                f"Description: {context.story_data.get('description')}\n"
            )
        logger.debug(f"[AGENT_PROMPT] Added story context: {context.story_data}")

    # --- Story Runtime State ---
    # Provides the agent with the user's live position in the story narrative.
    # This enables agents to respond contextually: referencing the current scene,
    # acknowledging the path taken, and guiding toward available choices.
    if context.story_runtime:
        rt = context.story_runtime
        conversation_context += "\n--- Current Story State ---\n"

        # Current node: what scene/moment the user is experiencing right now
        conversation_context += f"Current node: {rt.current_node_title}\n"
        if rt.current_node_content:
            conversation_context += f"Content: {rt.current_node_content}\n"
        if rt.current_node_type:
            conversation_context += f"Node type: {rt.current_node_type}\n"
        if rt.is_end_node:
            conversation_context += "⚠ This is an ending node in the story.\n"

        # Node chain: the breadcrumb trail showing how the user got here
        if rt.node_chain:
            path = " → ".join(rt.node_chain)
            conversation_context += f"Path taken: {path}\n"

        # Available choices: what the user can do next from this node
        if rt.available_choices:
            conversation_context += "Available choices:\n"
            for i, choice_text in enumerate(rt.available_choices, 1):
                conversation_context += f"  {i}. {choice_text}\n"

        # Story state: accumulated key-value state from prior choices
        # (e.g., {"has_key": true, "trust_level": 3})
        if rt.story_state:
            state_items = ", ".join(
                f"{k}={v}" for k, v in rt.story_state.items()
            )
            conversation_context += f"Story state: {state_items}\n"

        conversation_context += "---\n"
        logger.debug(f"[AGENT_PROMPT] Added story runtime: node={rt.current_node_title}")

    # Add other agents in the room (agent-aware prompting)
    if context.active_agents:
        other_agents = [
            agent for agent in context.active_agents if agent.slug != current_agent_slug
        ]
        if other_agents:
            conversation_context += "\nOther agents in this room:\n"
            for agent in other_agents:
                desc = agent.description or "Assistant"
                line = f"- {agent.name} (@{agent.slug}): {desc}"
                if agent.capabilities:
                    caps = ", ".join(agent.capabilities)
                    line += f" [Capabilities: {caps}]"
                conversation_context += line + "\n"
            conversation_context += (
                "\nYou can reference other agents with @mentions if their expertise is needed.\n"
            )

    # Add recent messages for conversation continuity
    # Exclude the trigger message to avoid duplication (it's appended at the end)
    if context.recent_messages:
        recent = [
            msg for msg in context.recent_messages[-5:]
            if msg.get("content") != trigger_message
        ]
        if recent:
            conversation_context += "\nRecent conversation:\n"
            for msg in recent:
                sender = msg.get("agent_name") or "User"
                conversation_context += f"{sender}: {msg.get('content', '')}\n"
                logger.debug(f"[AGENT_PROMPT] Added recent message from {sender}: {msg.get('content', '')}")

    # Add extra contexts if present
    if context.extra_contexts:
        logger.debug(f"[AGENT_PROMPT] Extra contexts: {context.extra_contexts}")
        rendered_extra_contexts = [
            rendered
            for item in context.extra_contexts
            if (rendered := render_extra_context_for_prompt(
                item,
                current_agent_slug=current_agent_slug,
            ))
        ]
        if rendered_extra_contexts:
            conversation_context += "\nAdditional context:\n"
            for rendered in rendered_extra_contexts:
                conversation_context += f"- {rendered}\n"

    # Combine context with user message
    if conversation_context:
        return f"{conversation_context}\nUser message: {trigger_message}"
        logger.debug(f"[AGENT_PROMPT] Built agent prompt with {conversation_context} for message: {trigger_message}")
    logger.debug(f"[AGENT_PROMPT] No additional context. Using trigger message as prompt: {trigger_message}")
    return trigger_message
