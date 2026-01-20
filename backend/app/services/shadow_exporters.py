from __future__ import annotations

import uuid
from typing import Any

from sqlmodel import Session, select

from app.models import (
    AgentConfig,
    AgentPersona,
    LLMModel,
    NodeChoice,
    Persona,
    PersonaQualityLink,
    PersonaTraitLink,
    Quality,
    QualityTraitLink,
    Room,
    RoomParticipant,
    RoomParticipantBinding,
    Story,
    StoryNode,
    StoryRequirement,
    StoryStateVariable,
    Trait,
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


def build_story_snapshot(*, session: Session, story_id: uuid.UUID) -> dict[str, Any]:
    story = session.get(Story, story_id)
    if not story:
        raise ValueError("Story not found")

    nodes = session.exec(
        select(StoryNode)
        .where(StoryNode.story_id == story_id)
        .order_by(StoryNode.story_version.asc(), StoryNode.created_at.asc())
    ).all()
    node_ids = [node.id for node in nodes]

    if node_ids:
        choices = session.exec(
            select(NodeChoice)
            .where(NodeChoice.from_node_id.in_(node_ids))
            .order_by(NodeChoice.from_node_id.asc())
        ).all()
    else:
        choices = []

    requirements = session.exec(
        select(StoryRequirement)
        .where(StoryRequirement.story_id == story_id)
        .order_by(StoryRequirement.id.asc())
    ).all()

    state_variables = session.exec(
        select(StoryStateVariable)
        .where(StoryStateVariable.story_id == story_id)
        .order_by(StoryStateVariable.story_version.asc(), StoryStateVariable.key.asc())
    ).all()

    return {
        "schema_version": 1,
        "entity_type": "story",
        "story": story.model_dump(mode="json"),
        "nodes": [node.model_dump(mode="json") for node in nodes],
        "choices": [choice.model_dump(mode="json") for choice in choices],
        "requirements": [req.model_dump(mode="json") for req in requirements],
        "state_variables": [var.model_dump(mode="json") for var in state_variables],
    }


def build_persona_snapshot(*, session: Session, persona_id: uuid.UUID) -> dict[str, Any]:
    persona = session.get(Persona, persona_id)
    if not persona:
        raise ValueError("Persona not found")

    trait_links = session.exec(
        select(PersonaTraitLink)
        .where(PersonaTraitLink.persona_id == persona_id)
        .order_by(PersonaTraitLink.created_at.asc())
    ).all()
    trait_ids = [link.trait_id for link in trait_links]
    traits = (
        session.exec(select(Trait).where(Trait.id.in_(trait_ids))).all()
        if trait_ids
        else []
    )

    quality_links = session.exec(
        select(PersonaQualityLink)
        .where(PersonaQualityLink.persona_id == persona_id)
        .order_by(PersonaQualityLink.created_at.asc())
    ).all()
    quality_ids = [link.quality_id for link in quality_links]
    qualities = (
        session.exec(select(Quality).where(Quality.id.in_(quality_ids))).all()
        if quality_ids
        else []
    )

    return {
        "schema_version": 1,
        "entity_type": "persona",
        "persona": persona.model_dump(mode="json"),
        "traits": [trait.model_dump(mode="json") for trait in traits],
        "qualities": [quality.model_dump(mode="json") for quality in qualities],
        "persona_trait_links": [link.model_dump(mode="json") for link in trait_links],
        "persona_quality_links": [link.model_dump(mode="json") for link in quality_links],
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


def build_quality_snapshot(*, session: Session, quality_id: uuid.UUID) -> dict[str, Any]:
    quality = session.get(Quality, quality_id)
    if not quality:
        raise ValueError("Quality not found")
    links = session.exec(
        select(QualityTraitLink)
        .where(QualityTraitLink.quality_id == quality_id)
        .order_by(QualityTraitLink.created_at.asc())
    ).all()
    return {
        "schema_version": 1,
        "entity_type": "quality",
        "quality": quality.model_dump(mode="json"),
        "quality_trait_links": [link.model_dump(mode="json") for link in links],
    }


def build_trait_snapshot(*, session: Session, trait_id: uuid.UUID) -> dict[str, Any]:
    trait = session.get(Trait, trait_id)
    if not trait:
        raise ValueError("Trait not found")
    links = session.exec(
        select(QualityTraitLink)
        .where(QualityTraitLink.trait_id == trait_id)
        .order_by(QualityTraitLink.created_at.asc())
    ).all()
    return {
        "schema_version": 1,
        "entity_type": "trait",
        "trait": trait.model_dump(mode="json"),
        "quality_trait_links": [link.model_dump(mode="json") for link in links],
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
