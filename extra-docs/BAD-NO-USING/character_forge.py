"""
CharacterForge Agent: AI assistant for character development and psychology.

This agent participates in rooms to help authors with:
- Character arc development
- Psychological depth and motivation
- Character relationships and dynamics
- Voice and personality consistency
- Backstory and growth trajectories
- Character-driven plot development

The agent is room-aware and uses story context when available.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.agents.agent_registry import register_agent
from app.services.context_provider import RoomContext

logger = logging.getLogger(__name__)


class CharacterForgeDeps(BaseModel):
    """Dependencies for CharacterForge agent tools."""

    model_config = {"arbitrary_types_allowed": True}

    context: RoomContext


# Create the agent
character_forge = Agent(
    "openai:gpt-4o-mini",
    deps_type=CharacterForgeDeps,
    system_prompt="""You are CharacterForge, an expert in character development and psychological depth.

Your expertise includes:
- Crafting compelling character arcs and transformation journeys
- Developing authentic psychological motivations and internal conflicts
- Creating distinct character voices and mannerisms
- Analyzing character relationships and dynamics
- Building believable backstories that inform present behavior
- Ensuring characters drive plot through their choices and growth
- Exploring character flaws, desires, fears, and contradictions

Your approach:
- Focus on what makes characters feel real and three-dimensional
- Ask probing questions about character motivations
- Suggest specific behaviors, choices, and conflicts that reveal character
- Help authors avoid stereotypes and create nuanced personalities
- Consider how characters challenge and complement each other
- Think about character arcs: who they are, who they become, and why

Keep responses practical and character-focused. Help authors create people
readers will remember, not just plot devices.""",
)


@character_forge.tool
async def get_story_characters(ctx: RunContext[CharacterForgeDeps]) -> str:
    """
    Get information about characters in the current story.

    Use this to understand what characters exist and their roles.
    """
    story_data = ctx.deps.context.story_data
    if not story_data:
        return "No story is currently associated with this room."

    return f"""Story: {story_data.get('title', 'Untitled')}

Description: {story_data.get('description', 'No description provided.')}

Review the story context to identify characters being discussed or developed."""


@character_forge.tool
async def get_recent_character_discussion(ctx: RunContext[CharacterForgeDeps]) -> str:
    """
    Get recent conversation about characters.

    Use this to understand what character aspects are being explored.
    """
    messages = ctx.deps.context.recent_messages
    if not messages:
        return "No previous messages in this conversation."

    summary_parts = []
    for msg in messages[-8:]:  # Focus on recent character discussions
        sender = msg.get("agent_name") or f"User {msg.get('sender_id', 'unknown')[:8]}"
        content = msg.get("content", "")[:250]
        summary_parts.append(f"- {sender}: {content}")

    return "Recent character discussion:\n" + "\n".join(summary_parts)


@character_forge.tool
async def analyze_character_patterns(ctx: RunContext[CharacterForgeDeps]) -> str:
    """
    Analyze conversation for character development patterns.

    Use this to identify what character elements the author is focusing on.
    """
    messages = ctx.deps.context.recent_messages
    if not messages or len(messages) < 2:
        return "Not enough conversation history to identify character patterns."

    all_content = " ".join(msg.get("content", "") for msg in messages)

    # Character-related keywords
    character_keywords = {
        "motivation": "character motivations",
        "arc": "character arcs",
        "relationship": "character relationships",
        "backstory": "backstory development",
        "personality": "personality traits",
        "growth": "character growth",
        "conflict": "internal/external conflicts",
        "voice": "character voice",
    }

    found_themes = [theme for keyword, theme in character_keywords.items()
                    if keyword in all_content.lower()]

    if found_themes:
        return f"Detected character development focus areas: {', '.join(found_themes)}"

    return "General character discussion detected. Ready to help with any aspect of character development."


@character_forge.tool
async def get_room_participants(ctx: RunContext[CharacterForgeDeps]) -> str:
    """
    Get list of participants in the current room.

    Use this to understand who is collaborating on character development.
    """
    participants = ctx.deps.context.participants
    if not participants:
        return "No participants found."

    parts = []
    for p in participants:
        ptype = p.get("participant_type", "unknown")
        pid = p.get("participant_id", "unknown")
        role = p.get("role", "member")

        if ptype == "agent":
            parts.append(f"- {pid} (agent)")
        else:
            parts.append(f"- User {pid[:8]}... ({role})")

    return "Room participants:\n" + "\n".join(parts)


# Register on module load
register_agent("CharacterForge", character_forge)


async def run_character_forge(
    user_message: str,
    context: RoomContext,
) -> str:
    """
    Run the CharacterForge agent with given context.

    Args:
        user_message: The message to respond to
        context: Room context with story data and conversation history

    Returns:
        Agent response text
    """
    deps = CharacterForgeDeps(context=context)

    # Build conversation context for the agent
    conversation_context = ""
    if context.story_data:
        conversation_context += (
            f"\nStory context: {context.story_data.get('title', 'Untitled')}\n"
        )
        if context.story_data.get('description'):
            conversation_context += f"Description: {context.story_data.get('description')}\n"

    if context.recent_messages:
        recent = context.recent_messages[-6:]  # Include more context for character work
        conversation_context += "\nRecent messages:\n"
        for msg in recent:
            sender = msg.get("agent_name") or "User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    full_prompt = f"{conversation_context}\nUser message: {user_message}"

    try:
        result = await character_forge.run(full_prompt, deps=deps)
        return result.output
    except Exception as e:
        logger.error(f"CharacterForge error: {e}")
        return "I apologize, but I encountered an error working on character development. Please try again."
