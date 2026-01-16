"""
DialogueCoach Agent: AI assistant for crafting natural, character-appropriate dialogue.

This agent participates in rooms to help authors with:
- Writing natural-sounding dialogue
- Ensuring character voice consistency
- Balancing dialogue with action and description
- Subtext and what characters don't say
- Dialect, rhythm, and speech patterns
- Dialogue that reveals character and advances plot
- Avoiding common dialogue pitfalls (info dumps, on-the-nose dialogue)

The agent is room-aware and uses story context when available.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.agents.agent_registry import register_agent
from app.services.context_provider import RoomContext

logger = logging.getLogger(__name__)


class DialogueCoachDeps(BaseModel):
    """Dependencies for DialogueCoach agent tools."""

    model_config = {"arbitrary_types_allowed": True}

    context: RoomContext


# Create the agent
dialogue_coach = Agent(
    "openai:gpt-4o-mini",
    deps_type=DialogueCoachDeps,
    system_prompt="""You are DialogueCoach, an expert in crafting authentic, compelling dialogue.

Your expertise includes:
- Writing dialogue that sounds natural when read aloud
- Creating distinct voices for different characters
- Using subtext (what's unsaid is often more important than what's said)
- Balancing dialogue with beats, action, and body language
- Avoiding exposition dumps disguised as conversation
- Crafting conflict and tension through dialogue
- Understanding rhythm, pacing, and the music of speech
- Regional dialects and speech patterns (when appropriate)
- Dialogue tags and attributions that enhance rather than distract

Your principles:
- Real people rarely say exactly what they mean
- Each character should have a distinct way of speaking
- Good dialogue does multiple things at once (reveals character, advances plot, creates tension)
- Less is often more; silence and pauses matter
- Avoid "as you know, Bob" exposition
- Dialogue should sound natural but be more focused than real speech
- Subtext creates depth; conflict creates energy

Your approach:
- Listen for authentic voice and rhythm
- Suggest specific word choices that fit character
- Point out when dialogue feels expository or on-the-nose
- Help authors layer in subtext and unspoken tension
- Recommend dialogue alternatives that show character
- Consider cultural, educational, and personality factors in speech patterns

Keep responses focused on the craft of dialogue. Help authors make characters
come alive through how they speak, what they avoid saying, and what their
words reveal about who they are.""",
)


@dialogue_coach.tool
async def get_character_voices(ctx: RunContext[DialogueCoachDeps]) -> str:
    """
    Get information about characters to understand their voices.

    Use this to ensure dialogue suggestions match character personalities.
    """
    story_data = ctx.deps.context.story_data
    if not story_data:
        return "No story is currently associated with this room."

    return f"""Story: {story_data.get('title', 'Untitled')}

Description: {story_data.get('description', 'No description provided.')}

Review the story context to understand character backgrounds and personalities that inform their speech."""


@dialogue_coach.tool
async def get_recent_dialogue(ctx: RunContext[DialogueCoachDeps]) -> str:
    """
    Get recent conversation about dialogue being crafted.

    Use this to understand what dialogue is being written or discussed.
    """
    messages = ctx.deps.context.recent_messages
    if not messages:
        return "No previous messages in this conversation."

    summary_parts = []
    for msg in messages[-8:]:
        sender = msg.get("agent_name") or f"User {msg.get('sender_id', 'unknown')[:8]}"
        content = msg.get("content", "")[:300]  # Longer excerpts for dialogue
        summary_parts.append(f"- {sender}: {content}")

    return "Recent dialogue discussion:\n" + "\n".join(summary_parts)


@dialogue_coach.tool
async def analyze_dialogue_patterns(ctx: RunContext[DialogueCoachDeps]) -> str:
    """
    Analyze conversation for dialogue-related discussions and patterns.

    Use this to identify what dialogue aspects the author is working on.
    """
    messages = ctx.deps.context.recent_messages
    if not messages or len(messages) < 2:
        return "Not enough conversation history to analyze dialogue patterns."

    all_content = " ".join(msg.get("content", "") for msg in messages)

    # Dialogue-related keywords
    dialogue_indicators = {
        "said": "dialogue tags and attribution",
        "voice": "character voice",
        "conversation": "conversational flow",
        "speak": "speech patterns",
        "dialect": "dialect and accent",
        "subtext": "subtext and implication",
        "argue": "conflict dialogue",
        "whisper": "tone and delivery",
        "quote": "quoted dialogue",
    }

    found_indicators = [desc for keyword, desc in dialogue_indicators.items()
                       if keyword in all_content.lower()]

    if found_indicators:
        return f"Dialogue focus areas detected: {', '.join(set(found_indicators))}"

    return "Ready to help with any aspect of dialogue writing, from character voice to subtext."


@dialogue_coach.tool
async def check_dialogue_balance(ctx: RunContext[DialogueCoachDeps]) -> str:
    """
    Check if recent discussion shows good balance between dialogue and other elements.

    Use this to advise on pacing and balance.
    """
    messages = ctx.deps.context.recent_messages
    if not messages:
        return "No messages to analyze for dialogue balance."

    # Count dialogue-heavy vs. description-heavy messages
    dialogue_markers = ['"', "'", "said", "asked", "replied", "spoke"]
    action_markers = ["walked", "looked", "moved", "felt", "thought", "saw"]

    all_content = " ".join(msg.get("content", "") for msg in messages).lower()

    dialogue_count = sum(1 for marker in dialogue_markers if marker in all_content)
    action_count = sum(1 for marker in action_markers if marker in all_content)

    if dialogue_count > action_count * 2:
        return "Detected dialogue-heavy discussion. Consider balancing with action and description."
    elif action_count > dialogue_count * 2:
        return "Detected description-heavy discussion. Dialogue might help vary the pace."

    return "Dialogue and narrative elements seem balanced. Ready to refine either aspect."


# Register on module load
register_agent("DialogueCoach", dialogue_coach)


async def run_dialogue_coach(
    user_message: str,
    context: RoomContext,
) -> str:
    """
    Run the DialogueCoach agent with given context.

    Args:
        user_message: The message to respond to
        context: Room context with story data and conversation history

    Returns:
        Agent response text
    """
    deps = DialogueCoachDeps(context=context)

    # Build conversation context for the agent
    conversation_context = ""
    if context.story_data:
        conversation_context += (
            f"\nStory context: {context.story_data.get('title', 'Untitled')}\n"
        )
        if context.story_data.get('description'):
            conversation_context += f"Description: {context.story_data.get('description')}\n"

    if context.recent_messages:
        recent = context.recent_messages[-6:]
        conversation_context += "\nRecent dialogue discussion:\n"
        for msg in recent:
            sender = msg.get("agent_name") or "User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    full_prompt = f"{conversation_context}\nUser message: {user_message}"

    try:
        result = await dialogue_coach.run(full_prompt, deps=deps)
        return result.output
    except Exception as e:
        logger.error(f"DialogueCoach error: {e}")
        return "I apologize, but I encountered an error working on dialogue. Please try again."
