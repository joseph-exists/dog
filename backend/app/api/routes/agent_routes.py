from fastapi import APIRouter, Request
from pydantic_ai.ui.ag_ui import AGUIAdapter
from starlette.responses import Response

from app.agents.quixote import agent
from app.models import AvailableAgent, AvailableAgentsPublic

router = APIRouter(prefix="/agents", tags=["agents"])

# ============================================================================
# Available Agents Registry (Task 5)
# ============================================================================
# This is the single source of truth for available agents.
# Previously hardcoded in frontend as AVAILABLE_AGENTS array.

AVAILABLE_AGENTS = [
    AvailableAgent(
        id="StoryAdvisor",
        name="Story Advisor",
        description="Helps with story structure, pacing, and narrative flow",
    ),
    AvailableAgent(
        id="SymbolWeaver",
        name="Symbol Weaver",
        description="Assists with themes, symbolism, and deeper meanings",
    ),
    AvailableAgent(
        id="CharacterForge",
        name="Character Forge",
        description="Develops character backgrounds, motivations, and arcs",
    ),
    AvailableAgent(
        id="PlotTwistArchitect",
        name="Plot Twist Architect",
        description="Creates surprising yet logical plot developments",
    ),
    AvailableAgent(
        id="DialogueCoach",
        name="Dialogue Coach",
        description="Improves character voice and conversational flow",
    ),
]


@router.get("/available", response_model=AvailableAgentsPublic)
def get_available_agents() -> AvailableAgentsPublic:
    """
    Get list of available agents for room participation.

    This endpoint provides the canonical list of agents that can be
    added to collaborative rooms. No authentication required.

    Returns:
        AvailableAgentsPublic with list of agents and count
    """
    return AvailableAgentsPublic(
        data=AVAILABLE_AGENTS,
        count=len(AVAILABLE_AGENTS),
    )


@router.post("/pydantic-agent")
async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent)
