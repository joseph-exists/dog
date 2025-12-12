from fastapi import APIRouter, Request
from starlette.responses import Response
from pydantic_ai.ui.ag_ui import AGUIAdapter
from app.agents.quixote import agent

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post('/pydantic-agent')
async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent)
