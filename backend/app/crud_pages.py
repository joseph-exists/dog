"""
CRUD operations for persisted page layouts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

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
    result = await session.exec(statement)
    return result.one_or_none()


async def get_page_by_id(session: AsyncSession, page_id: UUID) -> Page | None:
    """Fetch a page layout by page ID."""
    return await session.get(Page, page_id)


async def search_pages(
    session: AsyncSession,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    entity_type_prefix: str | None = None,
    entity_id_prefix: str | None = None,
    owner_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Page], int]:
    """Search page layouts with optional entity filters."""
    filters = []
    if entity_type:
        filters.append(Page.entity_type == entity_type)
    if entity_id:
        filters.append(Page.entity_id == entity_id)
    if entity_type_prefix:
        filters.append(Page.entity_type.startswith(entity_type_prefix))
    if entity_id_prefix:
        filters.append(Page.entity_id.startswith(entity_id_prefix))
    if owner_id:
        filters.append(Page.owner_id == owner_id)

    statement = (
        select(Page)
        .where(*filters)
        .order_by(desc(Page.updated_at))
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(statement)
    pages = result.all()

    count_statement = select(func.count()).select_from(Page).where(*filters)
    count_result = await session.exec(count_statement)
    count = count_result.one()
    return list(pages), count


async def create_page_layout(
    session: AsyncSession,
    *,
    owner_id: UUID,
    entity_type: str,
    entity_id: str,
    layout_json: list[dict[str, Any]],
    layout_version: int = 1,
    page_theme_id: UUID | None = None,
    cards_theme_id: UUID | None = None,
    presentation_json: dict[str, Any] | None = None,
) -> Page:
    """Create a new page layout for an entity."""
    page = Page(
        owner_id=owner_id,
        entity_type=entity_type,
        entity_id=entity_id,
        layout_json=layout_json,
        layout_version=layout_version,
        page_theme_id=page_theme_id,
        cards_theme_id=cards_theme_id,
        presentation_json=presentation_json or {},
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
    page_theme_id: UUID | None = None,
    cards_theme_id: UUID | None = None,
    presentation_json: dict[str, Any] | None = None,
) -> Page:
    """Update an existing page layout."""
    page.layout_json = layout_json
    if layout_version is not None:
        page.layout_version = layout_version
    page.page_theme_id = page_theme_id
    page.cards_theme_id = cards_theme_id
    page.presentation_json = presentation_json or {}
    page.updated_at = datetime.utcnow()
    session.add(page)
    await session.flush()
    await session.refresh(page)
    return page


async def delete_page_layout(session: AsyncSession, page: Page) -> None:
    """Delete a persisted page layout."""
    await session.delete(page)
    await session.flush()
