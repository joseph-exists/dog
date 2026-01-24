from __future__ import annotations

from typing import Any
import logging

logger = logging.getLogger(__name__)


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
        conversation_context += "\nAdditional context:\n"
        logger.debug(f"[AGENT_PROMPT] Extra contexts: {context.extra_contexts}")
        for item in context.extra_contexts:
            context_type = item.get("context_type", "unknown")
            source = item.get("source", "unknown")
            conversation_context += (
                f"- [{source}] {context_type}: {item.get('payload')}\n"
            )

    # Combine context with user message
    if conversation_context:
        return f"{conversation_context}\nUser message: {trigger_message}"
        logger.debug(f"[AGENT_PROMPT] Built agent prompt with {conversation_context} for message: {trigger_message}")
    logger.debug(f"[AGENT_PROMPT] No additional context. Using trigger message as prompt: {trigger_message}")
    return trigger_message 
