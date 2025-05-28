from fastapi import APIRouter

from app.api.routes import (
    items,
    personas,
    archetypes,
    login,
    private,
    users,
    utils,
    traits,
    qualities,
    events,
    quality_trait_links,
    persona_qualities,
    persona_events,
    stories,
    storynodes,
    user_personas,
    user_story_progress,
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
api_router.include_router(user_personas.router)
api_router.include_router(user_story_progress.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
