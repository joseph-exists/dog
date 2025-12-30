"""
SymbolWeaver Agent: AI assistant for symbolic interpretation and thematic analysis.

This agent participates in rooms to help authors with:
- Identifying and developing symbolic elements
- Analyzing themes and motifs
- Creating meaningful metaphors
- Ensuring symbolic consistency
- Exploring archetypal patterns

The agent is room-aware and uses story context when available.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.agents.agent_registry import register_agent
from app.services.context_provider import RoomContext

logger = logging.getLogger(__name__)


class SymbolWeaverDeps(BaseModel):
    """Dependencies for SymbolWeaver agent tools."""

    model_config = {"arbitrary_types_allowed": True}

    context: RoomContext


# Create the agent
symbol_weaver = Agent(
    "openai:gpt-4o-mini",
    deps_type=SymbolWeaverDeps,
    system_prompt="""You are SymbolWeaver, an expert in symbolic interpretation and thematic analysis.

Your expertise includes:
- Identifying symbolic patterns and motifs in stories
- Analyzing how symbols reinforce themes
- Suggesting archetypal resonances and mythological parallels
- Helping authors layer meaning through symbolism
- Ensuring symbols are consistent and purposeful throughout the narrative
- Exploring color symbolism, recurring images, and metaphorical structures

Your approach:
- Draw connections between symbols and deeper meanings
- Reference literary traditions and archetypal patterns when relevant
- Be specific about how symbols can be woven into plot and character development
- Avoid over-interpretation; symbols should serve the story, not overshadow it
- When analyzing existing story elements, look for symbolic potential

Keep responses insightful but accessible. Help authors create rich symbolic layers
without sacrificing clarity or narrative flow.""",
)


@symbol_weaver.tool
async def get_story_themes(ctx: RunContext[SymbolWeaverDeps]) -> str:
    """
    Get the current story's themes and symbolic elements.

    Use this to understand what themes the author is working with.
    """
    story_data = ctx.deps.context.story_data
    if not story_data:
        return "No story is currently associated with this room."

    return f"""Story: {story_data.get('title', 'Untitled')}

Description: {story_data.get('description', 'No description provided.')}

Use this context to identify existing or potential symbolic elements."""


@symbol_weaver.tool
async def get_conversation_context(ctx: RunContext[SymbolWeaverDeps]) -> str:
    """
    Get recent conversation to understand what symbols or themes are being discussed.
    """
    messages = ctx.deps.context.recent_messages
    if not messages:
        return "No previous messages in this conversation."

    summary_parts = []
    for msg in messages[-10:]:
        sender = msg.get("agent_name") or f"User {msg.get('sender_id', 'unknown')[:8]}"
        content = msg.get("content", "")[:200]
        summary_parts.append(f"- {sender}: {content}")

    return "Recent conversation:\n" + "\n".join(summary_parts)


@symbol_weaver.tool
async def analyze_symbolic_patterns(ctx: RunContext[SymbolWeaverDeps]) -> str:
    """
    Analyze the conversation history for recurring symbolic themes.

    Use this to identify patterns in what the author is exploring.
    """
    messages = ctx.deps.context.recent_messages
    if not messages or len(messages) < 3:
        return "Not enough conversation history to identify patterns."

    # Extract keywords that might indicate symbolic interests
    all_content = " ".join(msg.get("content", "") for msg in messages)

    # Simple pattern detection (could be enhanced)
    symbolic_keywords = [
        "symbol", "theme", "motif", "metaphor", "archetype",
        "meaning", "represent", "signify", "recurring"
    ]

    found_keywords = [kw for kw in symbolic_keywords if kw in all_content.lower()]

    if found_keywords:
        return f"Detected symbolic discussion themes: {', '.join(found_keywords)}"

    return "No explicit symbolic themes detected yet in the conversation."


# Register on module load
register_agent("SymbolWeaver", symbol_weaver)


async def run_symbol_weaver(
    user_message: str,
    context: RoomContext,
) -> str:
    """
    Run the SymbolWeaver agent with given context.

    Args:
        user_message: The message to respond to
        context: Room context with story data and conversation history

    Returns:
        Agent response text
    """
    deps = SymbolWeaverDeps(context=context)

    # Build conversation context for the agent
    conversation_context = ""
    if context.story_data:
        conversation_context += (
            f"\nStory context: {context.story_data.get('title', 'Untitled')}\n"
        )
        if context.story_data.get('description'):
            conversation_context += f"Description: {context.story_data.get('description')}\n"

    if context.recent_messages:
        recent = context.recent_messages[-5:]
        conversation_context += "\nRecent messages:\n"
        for msg in recent:
            sender = msg.get("agent_name") or "User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    full_prompt = f"{conversation_context}\nUser message: {user_message}"

    try:
        result = await symbol_weaver.run(full_prompt, deps=deps)
        return result.output
    except Exception as e:
        logger.error(f"SymbolWeaver error: {e}")
        return "I apologize, but I encountered an error analyzing the symbolic elements. Please try again."
