from __future__ import annotations

from typing import Any


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
    if context.recent_messages:
        recent = context.recent_messages[-5:]
        conversation_context += "\nRecent conversation:\n"
        for msg in recent:
            sender = msg.get("agent_name") or "User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    # Add extra contexts if present
    if context.extra_contexts:
        conversation_context += "\nAdditional context:\n"
        for item in context.extra_contexts:
            context_type = item.get("context_type", "unknown")
            source = item.get("source", "unknown")
            conversation_context += (
                f"- [{source}] {context_type}: {item.get('payload')}\n"
            )

    # Combine context with user message
    if conversation_context:
        return f"{conversation_context}\nUser message: {trigger_message}"
    return trigger_message
