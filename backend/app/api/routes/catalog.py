"""
Catalog Routes - Story Discovery (DISCOVERY Namespace)

Handles browsing and discovering published stories.
All endpoints filter to published stories only (is_published=True).

Endpoints:
- GET /catalog - Browse published stories
- GET /catalog/{story_id} - View published story details
- GET /catalog/{story_id}/nodes - Preview published story nodes
- GET /catalog/{story_id}/requirements - Check access requirements

Note: All endpoints return published_version data, not current_version drafts.
"""
# TODO: Add RBAC for requirement-based story access gating

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Story,
    StoryPublic,
    StoriesPublic,
    StoryNode,
    StoryNodePublic,
    StoryNodesPublic,
    StoryRequirement,
    StoryRequirementPublic,
    StoryRequirementsPublic,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/", response_model=StoriesPublic)
def read_catalog(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 10
) -> Any:
    """
    Retrieve published stories for catalog browsing.

    Superusers see all published stories.
    """
    count_statement = (
        select(func.count())
        .select_from(Story)
        .where(Story.is_published == True)  # noqa: E712
    )
    count = session.exec(count_statement).one()
    statement = (
        select(Story)
        .where(Story.is_published == True)  # noqa: E712
        .offset(skip)
        .limit(limit)
    )
    stories = session.exec(statement).all()

    return StoriesPublic(data=stories, count=count)


@router.get("/{story_id}", response_model=StoryPublic)
def read_catalog_story(
    session: SessionDep, current_user: CurrentUser, story_id: uuid.UUID
) -> Any:
    """
    Retrieve a published story by ID for catalog browsing.
    """
    story = session.get(Story, story_id)
    if not story or not story.is_published:
        raise HTTPException(status_code=404, detail="Published story not found")

    return story


@router.get("/{story_id}/nodes", response_model=StoryNodesPublic)
def read_catalog_story_nodes(
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve published story nodes for catalog preview.

    Returns nodes from the published_version, not current_version.
    This allows players to preview the story before starting it.
    """
    story = session.get(Story, story_id)
    if not story or not story.is_published:
        raise HTTPException(status_code=404, detail="Published story not found")

    # Get nodes from published_version only
    count_statement = (
        select(func.count())
        .select_from(StoryNode)
        .where(StoryNode.story_id == story_id)
        .where(StoryNode.story_version == story.published_version)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(StoryNode)
        .where(StoryNode.story_id == story_id)
        .where(StoryNode.story_version == story.published_version)
        .offset(skip)
        .limit(limit)
    )
    nodes = session.exec(statement).all()

    return StoryNodesPublic(data=nodes, count=count)


@router.get("/{story_id}/requirements", response_model=StoryRequirementsPublic)
def read_catalog_story_requirements(
    session: SessionDep, current_user: CurrentUser, story_id: uuid.UUID
) -> Any:
    """
    Retrieve story access requirements for catalog browsing.

    Returns the requirements (qualities, traits, etc.) needed to access this story.
    Frontend can use this to show "unlock requirements" or check if player can start.
    """
    story = session.get(Story, story_id)
    if not story or not story.is_published:
        raise HTTPException(status_code=404, detail="Published story not found")

    count_statement = (
        select(func.count())
        .select_from(StoryRequirement)
        .where(StoryRequirement.story_id == story_id)
    )
    count = session.exec(count_statement).one()

    statement = select(StoryRequirement).where(StoryRequirement.story_id == story_id)
    requirements = session.exec(statement).all()

    return StoryRequirementsPublic(data=requirements, count=count)
