from __future__ import annotations

import uuid
from typing import Any

from sqlmodel import Session, select

from app.models import (
    AgentConfig,
    AgentPersona,
    LLMModel,
    Persona,
    Room,
    RoomParticipant,
    RoomParticipantBinding,
    UserLLMProvider,
)


def build_room_snapshot(*, session: Session, room_id: uuid.UUID) -> dict[str, Any]:
    room = session.get(Room, room_id)
    if not room:
        raise ValueError("Room not found")

    participants = session.exec(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room_id)
        .order_by(RoomParticipant.joined_at.asc())
    ).all()

    bindings = session.exec(
        select(RoomParticipantBinding)
        .where(
            RoomParticipantBinding.room_id == room_id,
            RoomParticipantBinding.ended_at.is_(None),
        )
        .order_by(RoomParticipantBinding.effective_at.asc())
    ).all()

    return {
        "schema_version": 1,
        "entity_type": "room",
        "room": {
            "room_id": str(room.room_id),
            "creator_id": str(room.creator_id),
            "title": room.title,
            "story_id": str(room.story_id) if room.story_id else None,
            "created_at": room.created_at.isoformat() if room.created_at else None,
            "last_activity": room.last_activity.isoformat() if room.last_activity else None,
        },
        "participants": [
            {
                "id": str(p.id),
                "room_id": str(p.room_id),
                "participant_id": p.participant_id,
                "participant_type": p.participant_type,
                "role": p.role,
                "joined_at": p.joined_at.isoformat() if p.joined_at else None,
                "left_at": p.left_at.isoformat() if p.left_at else None,
                "active": p.active,
            }
            for p in participants
        ],
        "active_bindings": [
            {
                "id": str(b.id),
                "room_id": str(b.room_id),
                "participant_type": b.participant_type,
                "participant_id": b.participant_id,
                "user_id": str(b.user_id) if b.user_id else None,
                "agent_id": str(b.agent_id) if b.agent_id else None,
                "persona_id": str(b.persona_id) if b.persona_id else None,
                "model_name": b.model_name,
                "user_llm_provider_id": str(b.user_llm_provider_id) if b.user_llm_provider_id else None,
                "effective_at": b.effective_at.isoformat() if b.effective_at else None,
                "ended_at": b.ended_at.isoformat() if b.ended_at else None,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bindings
        ],
    }


def build_agent_snapshot(*, session: Session, agent_id: uuid.UUID) -> dict[str, Any]:
    agent = session.get(AgentConfig, agent_id)
    if not agent:
        raise ValueError("Agent not found")

    agent_personas = session.exec(
        select(AgentPersona)
        .where(AgentPersona.agent_id == agent_id)
        .order_by(AgentPersona.created_at.asc())
    ).all()

    return {
        "schema_version": 1,
        "entity_type": "agent",
        "agent": agent.model_dump(mode="json"),
        "agent_personas": [
            {
                "id": str(ap.id),
                "agent_id": str(ap.agent_id),
                "persona_id": str(ap.persona_id),
                "nickname": ap.nickname,
                "is_active": ap.is_active,
                "created_at": ap.created_at.isoformat() if ap.created_at else None,
                "updated_at": ap.updated_at.isoformat() if ap.updated_at else None,
            }
            for ap in agent_personas
        ],
    }


def build_persona_snapshot(*, session: Session, persona_id: uuid.UUID) -> dict[str, Any]:
    persona = session.get(Persona, persona_id)
    if not persona:
        raise ValueError("Persona not found")
    return {
        "schema_version": 1,
        "entity_type": "persona",
        "persona": persona.model_dump(mode="json"),
    }


def build_llm_model_snapshot(*, session: Session, llm_model_id: uuid.UUID) -> dict[str, Any]:
    llm_model = session.get(LLMModel, llm_model_id)
    if not llm_model:
        raise ValueError("LLM model not found")
    return {
        "schema_version": 1,
        "entity_type": "llm_model",
        "llm_model": llm_model.model_dump(mode="json"),
    }


def build_user_llm_provider_snapshot(
    *,
    session: Session,
    user_llm_provider_id: uuid.UUID,
) -> dict[str, Any]:
    provider = session.get(UserLLMProvider, user_llm_provider_id)
    if not provider:
        raise ValueError("User LLM provider not found")

    # Non-negotiable: never commit plaintext secrets to Shadow.
    # We also avoid committing encrypted secrets; store only an indicator.
    return {
        "schema_version": 1,
        "entity_type": "user_llm_provider",
        "user_llm_provider": {
            "id": str(provider.id),
            "user_id": str(provider.user_id),
            "provider_type": provider.provider_type,
            "name": provider.name,
            "is_enabled": provider.is_enabled,
            "is_default": provider.is_default,
            "base_url": provider.base_url,
            "description": provider.description,
            "api_key_present": provider.api_key_encrypted is not None and provider.api_key_encrypted != "",
            "created_at": provider.created_at.isoformat() if provider.created_at else None,
            "updated_at": provider.updated_at.isoformat() if provider.updated_at else None,
            "last_tested_at": provider.last_tested_at.isoformat() if provider.last_tested_at else None,
            "last_test_success": provider.last_test_success,
        },
    }

