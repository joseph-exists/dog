"""
CRUD operations for persisted page layouts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Page


async def get_page_by_entity(
    session: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> Page | None:
    """Fetch a page layout by entity type/id."""
    statement = select(Page).where(
        Page.entity_type == entity_type,
        Page.entity_id == entity_id,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_page_by_id(session: AsyncSession, page_id: UUID) -> Page | None:
    """Fetch a page layout by page ID."""
    return await session.get(Page, page_id)


async def create_page_layout(
    session: AsyncSession,
    *,
    owner_id: UUID,
    entity_type: str,
    entity_id: str,
    layout_json: list[dict[str, Any]],
    layout_version: int = 1,
) -> Page:
    """Create a new page layout for an entity."""
    page = Page(
        owner_id=owner_id,
        entity_type=entity_type,
        entity_id=entity_id,
        layout_json=layout_json,
        layout_version=layout_version,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(page)
    await session.flush()
    await session.refresh(page)
    return page


async def update_page_layout(
    session: AsyncSession,
    page: Page,
    *,
    layout_json: list[dict[str, Any]],
    layout_version: int | None = None,
) -> Page:
    """Update an existing page layout."""
    page.layout_json = layout_json
    if layout_version is not None:
        page.layout_version = layout_version
    page.updated_at = datetime.utcnow()
    session.add(page)
    await session.flush()
    await session.refresh(page)
    return page


async def delete_page_layout(session: AsyncSession, page: Page) -> None:
    """Delete a persisted page layout."""
    await session.delete(page)
    await session.flush()
