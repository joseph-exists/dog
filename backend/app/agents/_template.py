"""Template for creating AI Assistants using the PydanticAI model that is room-aware and uses available context."""

from __future__ import annotations

import logging

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.agents.agent_registry import register_agent
from app.services.context_provider import RoomContext

logger = logging.getLogger(__name__)

class ThisNewAgentDeps(BaseModel):
    """Dependencies for this agent's tools."""

    model_config = {"arbitrary_types_allowed":True}

    context: RoomContext

# create the agent
this_new_agent = Agent [ThisNewAgentDeps, str](
    ## TODO: update once we have typer functionality to create agents and modify their model parameters
    "openai:gpt-3.5-turbo-16k",
    deps_type=ThisNewAgentDeps,
    system_prompt="""You are ThisNewAgent, a new agent that is X and does Y.

Your expertise includes:
- things that help you do X
- Things that make X awesome
- Things that make Y great
- Details about Y.

Your principles:
- things that say things
- words about this agent's functions
- more things about them

Your approach:
- how this agent operates
- what things you do or suggest
- what you pay particular attention to

This is the final summary. Flavor and steering comments should go here.  How does this agent delight?""",
)

@this_new_agent.tool
async def what_tool_is(ctx: RunContext[ThisNewAgentDeps]) -> str:
    """tool stuff"""
    context_data = ctx.deps.context.context_data
    if not context_data:
        return "no context_data associated with this room"
    return f"""Context: {context_data.get('stuff that was in context', 'Context stuff')}

Description: {context_data.get('description', 'No description provided.')}

Published: {'Yes' if context_data.get('parameter_z') else 'No (parameter_z)'}

Analyze this for X Y Z"""

register_agent("ThisNewAgent", this_new_agent)

async def run_this_new_agent(
    user_message: str,
    context: RoomContext,
    ) -> str:
    """
    Run the ThisNewAgent agent with given context.

    Args:
        user_message: The message to respond to
        context: Room context with data and conversation history

    Returns:
        Agent response text
    """
    deps = ThisNewAgentDeps(context=context)

    # Build conversation context for the agent
    conversation_context = ""
    if context.context_data:
        conversation_context += (
            f"\ncontext: {context.context_data.get('stuff', 'Stuff')}\n"
        )
        if context.story_data.get('description'):
            conversation_context += f"Description: {context.context_data.get('description')}\n"

    if context.recent_messages:
        recent = context.recent_messages[-7:]  # More context for analysis
        conversation_context += "\nRecent discussion:\n"
        for msg in recent:
            sender = msg.get("agent_name") or "User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    full_prompt = f"{conversation_context}\nUser message: {user_message}"

    try:
        result = await this_new_agent.run(full_prompt, deps=deps)
        return result.output
    except Exception as e:
        logger.error(f"ThisNewAgent error: {e}")
        return "I apologize, but I encountered an error. Please try again."


