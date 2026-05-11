from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models import (
    Room,
    RoomParticipant,
    ShadowRepo,
    User,
    WorkspaceBootstrapIntent,
    WorkspaceCreate,
    WorkspaceShadowRepoSource,
)
from app.services.workspace_bootstrap_service import WorkspaceBootstrapValidationError
from app.services.workspace_service import normalize_bootstrap_intent


async def _create_room_with_owner(
    session: AsyncSession,
) -> tuple[uuid.UUID, uuid.UUID]:
    owner = User(
        email=f"workspace-shadow-{uuid.uuid4()}@example.com",
        hashed_password="test",
    )
    session.add(owner)
    await session.flush()

    room = Room(
        room_id=uuid.uuid4(),
        creator_id=owner.id,
        title="Workspace Shadow Room",
        story_id=None,
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    session.add(room)
    session.add(
        RoomParticipant(
            room_id=room.room_id,
            participant_id=str(owner.id),
            participant_type="user",
            role="owner",
            active=True,
        )
    )
    await session.commit()
    return room.room_id, owner.id


@pytest.mark.asyncio
async def test_normalize_bootstrap_intent_accepts_room_shadow_repo(
    async_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "SHADOW_REPO_URL_TEMPLATE",
        "https://git.example/shadow/{entity_type}-{entity_id}.git",
    )
    room_id, owner_id = await _create_room_with_owner(async_session)

    normalized = await normalize_bootstrap_intent(
        async_session,
        owner_id=owner_id,
        req=WorkspaceCreate(
            name="Room Workspace",
            bootstrap=WorkspaceBootstrapIntent(
                repo_source=WorkspaceShadowRepoSource(
                    entity_type="room",
                    entity_id=room_id,
                    ref="main",
                )
            ),
        ),
    )

    assert (
        normalized.materialized_repo_url
        == f"https://git.example/shadow/room-{room_id}.git"
    )
    clone_steps = [
        step for step in normalized.plan.steps if step.type == "clone_repo"
    ]
    assert len(clone_steps) == 1
    assert clone_steps[0].ref == "main"

    shadow_repo = (
        await async_session.exec(
            select(ShadowRepo).where(
                ShadowRepo.entity_type == "room",
                ShadowRepo.entity_id == room_id,
            )
        )
    ).first()
    assert shadow_repo is not None


@pytest.mark.asyncio
async def test_normalize_bootstrap_intent_rejects_shadow_repo_without_remote(
    async_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "SHADOW_REPO_URL_TEMPLATE", None)
    room_id, owner_id = await _create_room_with_owner(async_session)

    with pytest.raises(WorkspaceBootstrapValidationError) as exc_info:
        await normalize_bootstrap_intent(
            async_session,
            owner_id=owner_id,
            req=WorkspaceCreate(
                name="Room Workspace",
                bootstrap=WorkspaceBootstrapIntent(
                    repo_source=WorkspaceShadowRepoSource(
                        entity_type="room",
                        entity_id=room_id,
                    )
                ),
            ),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "WORKSPACE_SHADOW_REPO_REMOTE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_normalize_bootstrap_intent_rejects_non_room_shadow_repo(
    async_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "SHADOW_REPO_URL_TEMPLATE",
        "https://git.example/shadow/{entity_type}-{entity_id}.git",
    )
    _room_id, owner_id = await _create_room_with_owner(async_session)

    with pytest.raises(WorkspaceBootstrapValidationError) as exc_info:
        await normalize_bootstrap_intent(
            async_session,
            owner_id=owner_id,
            req=WorkspaceCreate(
                name="Agent Workspace",
                bootstrap=WorkspaceBootstrapIntent(
                    repo_source=WorkspaceShadowRepoSource(
                        entity_type="agent",
                        entity_id=uuid.uuid4(),
                    )
                ),
            ),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "WORKSPACE_SHADOW_REPO_ENTITY_UNSUPPORTED"
