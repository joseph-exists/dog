"""
PlotTwistArchitect Agent: AI assistant for crafting surprising yet logical plot developments.

This agent participates in rooms to help authors with:
- Designing effective plot twists
- Ensuring twists are foreshadowed properly
- Maintaining logical consistency while surprising readers
- Identifying twist opportunities in existing narratives
- Balancing revelation and concealment
- Creating "aha!" moments that feel earned

The agent is room-aware and uses story context when available.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.agents.agent_registry import register_agent
from app.services.context_provider import RoomContext

logger = logging.getLogger(__name__)


class PlotTwistArchitectDeps(BaseModel):
    """Dependencies for PlotTwistArchitect agent tools."""

    model_config = {"arbitrary_types_allowed": True}

    context: RoomContext


# Create the agent
plot_twist_architect = Agent(
    "openai:gpt-4o-mini",
    deps_type=PlotTwistArchitectDeps,
    system_prompt="""You are PlotTwistArchitect, a master of narrative surprise and revelation.

Your expertise includes:
- Designing plot twists that feel both surprising and inevitable
- Identifying opportunities for meaningful revelations in story structure
- Ensuring proper foreshadowing without telegraphing the twist
- Balancing misdirection with fair play to the reader
- Creating layered twists that recontextualize earlier events
- Avoiding twist pitfalls (deus ex machina, character betrayal, cheap shocks)
- Timing revelations for maximum emotional impact

Your principles:
- Great twists are hidden in plain sight through careful setup
- Every twist should reframe the story in a meaningful way
- Foreshadowing should exist but only be obvious in retrospect
- Character consistency matters even through revelations
- The best twists make readers want to reread/rewatch
- Avoid twists for shock value alone; they must serve the story

Your approach:
- Ask about existing plot points to identify twist opportunities
- Suggest specific foreshadowing techniques
- Help authors layer in clues without making them obvious
- Ensure twists enhance rather than undermine the narrative
- Consider reader expectations and how to subvert them thoughtfully

Keep responses strategic and spoiler-conscious. Help authors craft
moments that will make readers gasp, then smile in appreciation.""",
)


@plot_twist_architect.tool
async def get_story_plot(ctx: RunContext[PlotTwistArchitectDeps]) -> str:
    """
    Get the current story's plot structure and key events.

    Use this to identify potential twist opportunities.
    """
    story_data = ctx.deps.context.story_data
    if not story_data:
        return "No story is currently associated with this room."

    return f"""Story: {story_data.get('title', 'Untitled')}

Description: {story_data.get('description', 'No description provided.')}

Published: {'Yes' if story_data.get('is_published') else 'No (draft)'}

Analyze this for potential twist opportunities and existing narrative threads."""


@plot_twist_architect.tool
async def get_narrative_threads(ctx: RunContext[PlotTwistArchitectDeps]) -> str:
    """
    Get recent conversation to identify narrative threads and plot points.

    Use this to understand what story elements are in play.
    """
    messages = ctx.deps.context.recent_messages
    if not messages:
        return "No previous messages in this conversation."

    summary_parts = []
    for msg in messages[-10:]:
        sender = msg.get("agent_name") or f"User {msg.get('sender_id', 'unknown')[:8]}"
        content = msg.get("content", "")[:200]
        summary_parts.append(f"- {sender}: {content}")

    return "Recent narrative discussion:\n" + "\n".join(summary_parts)


@plot_twist_architect.tool
async def analyze_twist_setup(ctx: RunContext[PlotTwistArchitectDeps]) -> str:
    """
    Analyze the conversation for existing plot elements that could support twists.

    Use this to identify setup opportunities and potential payoffs.
    """
    messages = ctx.deps.context.recent_messages
    if not messages or len(messages) < 3:
        return "Not enough narrative discussion to analyze twist potential."

    all_content = " ".join(msg.get("content", "") for msg in messages)

    # Plot-related keywords that suggest twist opportunities
    twist_indicators = {
        "secret": "hidden information or secrets",
        "reveal": "planned revelations",
        "surprise": "surprise elements",
        "foreshadow": "foreshadowing setup",
        "mystery": "mysterious elements",
        "hidden": "concealed plot points",
        "unexpected": "unexpected developments",
        "truth": "hidden truths",
    }

    found_indicators = [desc for keyword, desc in twist_indicators.items()
                       if keyword in all_content.lower()]

    if found_indicators:
        return f"Potential twist elements detected: {', '.join(found_indicators)}"

    return "Analyzing narrative for twist opportunities. Ready to help plant seeds or craft revelations."


@plot_twist_architect.tool
async def check_story_consistency(ctx: RunContext[PlotTwistArchitectDeps]) -> str:
    """
    Review conversation for plot consistency to ensure twists don't break logic.

    Use this before suggesting twists that might contradict established facts.
    """
    messages = ctx.deps.context.recent_messages
    if not messages:
        return "No conversation history to check consistency."

    # Simple check for contradictory statements (could be enhanced)
    return "Reviewing established story facts for consistency. Ensure any twist aligns with what's been established."


# Register on module load
register_agent("PlotTwistArchitect", plot_twist_architect)


async def run_plot_twist_architect(
    user_message: str,
    context: RoomContext,
) -> str:
    """
    Run the PlotTwistArchitect agent with given context.

    Args:
        user_message: The message to respond to
        context: Room context with story data and conversation history

    Returns:
        Agent response text
    """
    deps = PlotTwistArchitectDeps(context=context)

    # Build conversation context for the agent
    conversation_context = ""
    if context.story_data:
        conversation_context += (
            f"\nStory context: {context.story_data.get('title', 'Untitled')}\n"
        )
        if context.story_data.get('description'):
            conversation_context += f"Description: {context.story_data.get('description')}\n"

    if context.recent_messages:
        recent = context.recent_messages[-7:]  # More context for plot analysis
        conversation_context += "\nRecent plot discussion:\n"
        for msg in recent:
            sender = msg.get("agent_name") or "User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    full_prompt = f"{conversation_context}\nUser message: {user_message}"

    try:
        result = await plot_twist_architect.run(full_prompt, deps=deps)
        return result.output
    except Exception as e:
        logger.error(f"PlotTwistArchitect error: {e}")
        return "I apologize, but I encountered an error analyzing plot possibilities. Please try again."
