from fastapi import APIRouter

from app.api.routes import (
    agent_personas,
    agent_routes,
    archetypes,
    catalog,
    events,
    items,
    llm_catalog,
    llm_providers,
    login,
    node_choices,
    persona_events,
    persona_qualities,
    personas,
    pages,
    presets,
    private,
    qualities,
    quality_trait_links,
    room_panels,
    room_participant_bindings,
    room_contexts,
    room_agent_settings,
    room_runtime,
    rooms,
    stories,
    storynodes,
    trait_conflicts,
    traits,
    user_panels,
    user_personas,
    user_story_progress,
    users,
    utils,
    websocket,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(personas.router)
api_router.include_router(archetypes.router)
api_router.include_router(qualities.router)
api_router.include_router(traits.router)
api_router.include_router(events.router)
api_router.include_router(quality_trait_links.router)
api_router.include_router(persona_qualities.router)
api_router.include_router(persona_events.router)
api_router.include_router(storynodes.router)
api_router.include_router(stories.router)
api_router.include_router(catalog.router)
api_router.include_router(user_personas.router)
api_router.include_router(user_story_progress.router)
api_router.include_router(agent_routes.router)
api_router.include_router(agent_personas.router)
api_router.include_router(llm_providers.router)
api_router.include_router(llm_catalog.router)
api_router.include_router(rooms.router)
api_router.include_router(room_contexts.router)
api_router.include_router(room_agent_settings.router)
api_router.include_router(room_runtime.router)
api_router.include_router(pages.router)
api_router.include_router(room_panels.router, prefix="/rooms", tags=["room-panels"])
api_router.include_router(room_participant_bindings.router)
api_router.include_router(node_choices.router)
api_router.include_router(websocket.router)
api_router.include_router(trait_conflicts.router)
api_router.include_router(user_panels.router, prefix="/users", tags=["user-panels"])
api_router.include_router(presets.router, prefix="/presets", tags=["presets"])

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
