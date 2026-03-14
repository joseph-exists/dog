"""
API routes for panel presets.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


# System presets (not stored in DB)
SYSTEM_PRESETS = {
    "focus": {
        "id": "focus",
        "name": "Focus",
        "description": "Chat only, full width",
        "panels": [{"id": "chat", "kind": "chat", "prominence": "primary"}],
        "is_system": True,
    },
    "classic": {
        "id": "classic",
        "name": "Classic",
        "description": "Chat with participants sidebar (V1 style)",
        "panels": [
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {"id": "participants", "kind": "participantPanel", "prominence": "auxiliary"},
        ],
        "is_system": True,
    },
    "collaborate": {
        "id": "collaborate",
        "name": "Collaborate",
        "description": "Chat with participants sidebar",
        "panels": [
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {
                "id": "participants",
                "kind": "participantPanel",
                "prominence": "auxiliary",
            },
        ],
        "is_system": True,
    },
    "story_mode": {
        "id": "story_mode",
        "name": "Story Mode",
        "description": "Story editor with chat",
        "panels": [
            {"id": "story", "kind": "storyEditor", "prominence": "primary"},
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {
                "id": "participants",
                "kind": "participantPanel",
                "prominence": "auxiliary",
            },
        ],
        "is_system": True,
    },
    "debug": {
        "id": "debug",
        "name": "Debug",
        "description": "Chat with debug info",
        "panels": [
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {"id": "debug", "kind": "debug", "prominence": "auxiliary"},
            {
                "id": "participants",
                "kind": "participantPanel",
                "prominence": "auxiliary",
            },
        ],
        "is_system": True,
    },
    "canvas": {
        "id": "canvas",
        "name": "Canvas",
        "description": "Canvas with chat",
        "panels": [
            {"id": "canvas", "kind": "canvas", "prominence": "primary"},
            {"id": "chat", "kind": "chat", "prominence": "primary"},
            {
                "id": "participants",
                "kind": "participantPanel",
                "prominence": "auxiliary",
            },
        ],
        "is_system": True,
    },
}


class PresetResponse(BaseModel):
    id: str
    name: str
    description: str
    panels: list[dict]
    is_system: bool


class PresetsListResponse(BaseModel):
    presets: list[PresetResponse]


@router.get("", response_model=PresetsListResponse)
async def list_presets() -> Any:
    """List all available presets (system presets only for now)."""
    return PresetsListResponse(
        presets=[PresetResponse(**p) for p in SYSTEM_PRESETS.values()]
    )


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(preset_id: str) -> Any:
    """Get a specific preset by ID."""
    preset = SYSTEM_PRESETS.get(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return PresetResponse(**preset)
