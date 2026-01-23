"""
API routes for persisted page layouts.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud_pages import (
    create_page_layout,
    delete_page_layout,
    get_page_by_entity,
    get_page_by_id,
    search_pages,
    update_page_layout,
)
from app.models import PageLayoutUpdate, PagePublic, PagesPublic

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("/", response_model=PagesPublic)
async def list_pages(
    *,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    entity_type: str | None = None,
    entity_id: str | None = None,
    entity_type_prefix: str | None = None,
    entity_id_prefix: str | None = None,
) -> Any:
    """Search persisted page layouts."""
    owner_id = None if current_user.is_superuser else current_user.id
    pages, count = await search_pages(
        session,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_type_prefix=entity_type_prefix,
        entity_id_prefix=entity_id_prefix,
        owner_id=owner_id,
        skip=skip,
        limit=limit,
    )
    return PagesPublic(
        data=[PagePublic.model_validate(page) for page in pages],
        count=count,
    )


@router.get("/{entity_type}/{entity_id}", response_model=PagePublic | None)
async def get_page_layout(
    *,
    entity_type: str,
    entity_id: str,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get the persisted page layout for an entity."""
    return await get_page_by_entity(session, entity_type, entity_id)


@router.post("/{entity_type}/{entity_id}/layout", response_model=PagePublic)
async def upsert_page_layout(
    *,
    entity_type: str,
    entity_id: str,
    payload: PageLayoutUpdate,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """Create or overwrite a page layout for an entity."""
    existing = await get_page_by_entity(session, entity_type, entity_id)
    if existing:
        if existing.owner_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
        return await update_page_layout(
            session,
            existing,
            layout_json=payload.layout_json,
            layout_version=payload.layout_version,
        )

    return await create_page_layout(
        session,
        owner_id=current_user.id,
        entity_type=entity_type,
        entity_id=entity_id,
        layout_json=payload.layout_json,
        layout_version=payload.layout_version or 1,
    )


@router.put("/{page_id}", response_model=PagePublic)
async def update_page(
    *,
    page_id: UUID,
    payload: PageLayoutUpdate,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """Update an existing page layout by page ID."""
    page = await get_page_by_id(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if page.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    return await update_page_layout(
        session,
        page,
        layout_json=payload.layout_json,
        layout_version=payload.layout_version,
    )


@router.delete("/{page_id}")
async def delete_page(
    *,
    page_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> dict[str, str]:
    """Delete a persisted page layout."""
    page = await get_page_by_id(session, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if page.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    await delete_page_layout(session, page)
    return {"message": "Page deleted successfully"}
