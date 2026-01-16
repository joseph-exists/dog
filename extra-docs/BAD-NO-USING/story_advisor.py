"""
StoryAdvisor Agent: AI assistant for story writing and development.

This agent participates in rooms to help authors with:
- Story structure and pacing
- Character development
- Plot consistency
- Writing suggestions

The agent is room-aware and uses story context when available.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.agents.agent_registry import register_agent
from app.services.context_provider import RoomContext

logger = logging.getLogger(__name__)


class StoryAdvisorDeps(BaseModel):
    """Dependencies for StoryAdvisor agent tools."""

    model_config = {"arbitrary_types_allowed": True}

    context: RoomContext


# Create the agent
story_advisor = Agent(
    "openai:gpt-4o-mini",  # Cost-effective for advisory tasks
    deps_type=StoryAdvisorDeps,
    system_prompt="""You are StoryAdvisor, an expert writing assistant who helps authors develop their stories.

Your responsibilities:
- Provide constructive feedback on story elements
- Help with plot development and pacing
- Suggest character arcs and motivations
- Maintain consistency with established story details
- Be encouraging while offering specific, actionable suggestions

When you have story context available, reference specific details from the story.
When responding in a room with multiple participants, be conversational and address
the group naturally.

Keep responses concise but helpful. Avoid generic advice - be specific to the story
and conversation context provided.""",
)


@story_advisor.tool
async def get_story_outline(ctx: RunContext[StoryAdvisorDeps]) -> str:
    """
    Get the current story's outline and description.

    Use this tool when you need to reference story details to provide
    contextual advice.
    """
    story_data = ctx.deps.context.story_data
    if not story_data:
        return "No story is currently associated with this room."

    return f"""Story: {story_data.get('title', 'Untitled')}

Description: {story_data.get('description', 'No description provided.')}

Published: {'Yes' if story_data.get('is_published') else 'No (draft)'}"""


@story_advisor.tool
async def get_conversation_summary(ctx: RunContext[StoryAdvisorDeps]) -> str:
    """
    Get a summary of recent conversation in the room.

    Use this to understand what has been discussed before responding.
    """
    messages = ctx.deps.context.recent_messages
    if not messages:
        return "No previous messages in this conversation."

    summary_parts = []
    for msg in messages[-10:]:  # Last 10 messages for summary
        sender = msg.get("agent_name") or f"User {msg.get('sender_id', 'unknown')[:8]}"
        content = msg.get("content", "")[:200]  # Truncate long messages
        summary_parts.append(f"- {sender}: {content}")

    return "Recent conversation:\n" + "\n".join(summary_parts)


@story_advisor.tool
async def get_room_participants(ctx: RunContext[StoryAdvisorDeps]) -> str:
    """
    Get list of participants in the current room.

    Use this to understand who is in the conversation.
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
register_agent("StoryAdvisor", story_advisor)


async def run_story_advisor(
    user_message: str,
    context: RoomContext,
) -> str:
    """
    Run the StoryAdvisor agent with given context.

    Args:
        user_message: The message to respond to
        context: Room context with story data and conversation history

    Returns:
        Agent response text
    """
    deps = StoryAdvisorDeps(context=context)

    # Build conversation context for the agent
    conversation_context = ""
    if context.story_data:
        conversation_context += (
            f"\nStory context: {context.story_data.get('title', 'Untitled')}\n"
        )

    if context.recent_messages:
        recent = context.recent_messages[-5:]  # Include last 5 messages
        conversation_context += "\nRecent messages:\n"
        for msg in recent:
            sender = msg.get("agent_name") or "User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    full_prompt = f"{conversation_context}\nUser message: {user_message}"

    try:
        result = await story_advisor.run(full_prompt, deps=deps)
        return result.output
    except Exception as e:
        logger.error(f"StoryAdvisor error: {e}")
        return "I apologize, but I encountered an error processing your request. Please try again."
