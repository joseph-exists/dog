from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def summarize_room(snapshot_json: dict[str, Any]) -> dict[str, Any]:
    room = snapshot_json.get("room") or snapshot_json
    participants = snapshot_json.get("participants", [])
    active_bindings = snapshot_json.get("active_bindings", [])

    return {
        "room": {
            "room_id": room.get("room_id"),
            "title": room.get("title"),
            "story_id": room.get("story_id"),
            "created_at": room.get("created_at"),
            "last_activity": room.get("last_activity"),
        },
        "participants": [
            {
                "participant_id": p.get("participant_id"),
                "participant_type": p.get("participant_type"),
                "role": p.get("role"),
                "active": p.get("active"),
            }
            for p in participants
        ],
        "active_bindings": [
            {
                "participant_type": b.get("participant_type"),
                "participant_id": b.get("participant_id"),
                "persona_id": b.get("persona_id"),
                "model_name": b.get("model_name"),
                "user_llm_provider_id": b.get("user_llm_provider_id"),
                "effective_at": b.get("effective_at"),
            }
            for b in active_bindings
        ],
    }


def summarize_story(snapshot_json: dict[str, Any]) -> dict[str, Any]:
    story = snapshot_json.get("story") or snapshot_json
    return {
        "story": {
            "id": story.get("id"),
            "title": story.get("title"),
            "description": story.get("description"),
            "is_published": story.get("is_published"),
            "current_version": story.get("current_version"),
            "published_version": story.get("published_version"),
        }
    }


def summarize_agent(snapshot_json: dict[str, Any]) -> dict[str, Any]:
    agent = snapshot_json.get("agent") or snapshot_json
    personas = snapshot_json.get("agent_personas", [])
    return {
        "agent": {
            "id": agent.get("id"),
            "slug": agent.get("slug"),
            "name": agent.get("name"),
            "description": agent.get("description"),
            "participation_mode": agent.get("participation_mode"),
            "capabilities": agent.get("capabilities", []),
        },
        "agent_personas": [
            {
                "persona_id": p.get("persona_id"),
                "nickname": p.get("nickname"),
                "is_active": p.get("is_active"),
            }
            for p in personas
        ],
    }


def summarize_persona(snapshot_json: dict[str, Any]) -> dict[str, Any]:
    persona = snapshot_json.get("persona") or snapshot_json
    return {
        "persona": {
            "id": persona.get("id"),
            "name": persona.get("name"),
            "description": persona.get("description"),
            "long_description": persona.get("long_description"),
        }
    }


def summarize_llm_model(snapshot_json: dict[str, Any]) -> dict[str, Any]:
    model = snapshot_json.get("llm_model") or snapshot_json
    return {
        "llm_model": {
            "id": model.get("id"),
            "model_id": model.get("model_id"),
            "display_name": model.get("display_name"),
            "description": model.get("description"),
            "context_window": model.get("context_window"),
            "provider_id": model.get("provider_id"),
            "is_default": model.get("is_default"),
            "is_enabled": model.get("is_enabled"),
        }
    }


def summarize_user_llm_provider(snapshot_json: dict[str, Any]) -> dict[str, Any]:
    provider = snapshot_json.get("user_llm_provider") or snapshot_json
    # Non-negotiable: never surface api_key / api_key_encrypted in summaries.
    if provider.get("provider_type") is not None:
        # Legacy payloads used provider_type name; fail fast and log loudly.
        logger.error("Legacy provider_type found in user_llm_provider snapshot payload")
    return {
        "user_llm_provider": {
            "id": provider.get("id"),
            "user_id": provider.get("user_id"),
            "provider_type_id": provider.get("provider_type_id"),
            "name": provider.get("name"),
            "is_enabled": provider.get("is_enabled"),
            "is_default": provider.get("is_default"),
            "base_url": provider.get("base_url"),
            "description": provider.get("description"),
            "api_key_present": provider.get("api_key_present"),
            "last_tested_at": provider.get("last_tested_at"),
            "last_test_success": provider.get("last_test_success"),
        }
    }


SUMMARY_DISPATCH = {
    "room": summarize_room,
    "story": summarize_story,
    "agent": summarize_agent,
    "persona": summarize_persona,
    "llm_model": summarize_llm_model,
    "user_llm_provider": summarize_user_llm_provider,
}
