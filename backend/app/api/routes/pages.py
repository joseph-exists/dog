"""
API routes for persisted page layouts.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import (
    AsyncSessionDep,
    AsyncSessionTransactionDep,
    CurrentUser,
    OptionalUser,
)
from app.crud_pages import (
    create_page_layout,
    delete_page_layout,
    get_page_by_entity,
    get_page_by_id,
    search_pages,
    update_page_layout,
)
from app.models import (
    AccessGrantRole,
    PageLayoutUpdate,
    PagePublic,
    PagesPublic,
    ResolvedUserPageAudiencePublic,
)
from app.services.access_control import require_access, resolve_user_page_audience

router = APIRouter(prefix="/pages", tags=["pages"])


def _parse_project_entity_uuid(entity_id: str) -> UUID:
    try:
        return UUID(entity_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid project entity_id") from exc


async def _require_project_page_access(
    *,
    session: AsyncSessionDep | AsyncSessionTransactionDep,
    current_user: CurrentUser,
    entity_id: str,
    minimum_role: AccessGrantRole,
) -> None:
    project_id = _parse_project_entity_uuid(entity_id)
    await require_access(
        session,
        user=current_user,
        resource_type="project",
        resource_id=project_id,
        minimum_role=minimum_role,
        detail="Access denied",
    )


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
    current_user: OptionalUser,
) -> Any:
    """Get the persisted page layout for an entity."""
    if entity_type == "project":
        if current_user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        await _require_project_page_access(
            session=session,
            current_user=current_user,
            entity_id=entity_id,
            minimum_role=AccessGrantRole.viewer,
        )
    return await get_page_by_entity(session, entity_type, entity_id)


@router.get(
    "/{entity_type}/{entity_id}/audience",
    response_model=ResolvedUserPageAudiencePublic,
)
async def resolve_page_audience(
    *,
    entity_type: str,
    entity_id: str,
    session: AsyncSessionDep,
    current_user: OptionalUser,
) -> Any:
    if entity_type != "user":
        raise HTTPException(status_code=400, detail="Audience resolution is only supported for user pages")

    page = await get_page_by_entity(session, entity_type, entity_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return await resolve_user_page_audience(
        session,
        page=page,
        viewer=current_user,
    )


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
    if entity_type == "project":
        await _require_project_page_access(
            session=session,
            current_user=current_user,
            entity_id=entity_id,
            minimum_role=AccessGrantRole.editor,
        )

    existing = await get_page_by_entity(session, entity_type, entity_id)
    if existing:
        if (
            entity_type != "project"
            and existing.owner_id != current_user.id
            and not current_user.is_superuser
        ):
            raise HTTPException(status_code=403, detail="Access denied")
        return await update_page_layout(
            session,
            existing,
            layout_json=payload.layout_json,
            layout_version=payload.layout_version,
            page_theme_id=payload.page_theme_id,
            cards_theme_id=payload.cards_theme_id,
            presentation_json=payload.presentation_json,
        )

    return await create_page_layout(
        session,
        owner_id=current_user.id,
        entity_type=entity_type,
        entity_id=entity_id,
        layout_json=payload.layout_json,
        layout_version=payload.layout_version or 1,
        page_theme_id=payload.page_theme_id,
        cards_theme_id=payload.cards_theme_id,
        presentation_json=payload.presentation_json,
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

    if page.entity_type == "project":
        await _require_project_page_access(
            session=session,
            current_user=current_user,
            entity_id=page.entity_id,
            minimum_role=AccessGrantRole.editor,
        )
    elif page.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    return await update_page_layout(
        session,
        page,
        layout_json=payload.layout_json,
        layout_version=payload.layout_version,
        page_theme_id=payload.page_theme_id,
        cards_theme_id=payload.cards_theme_id,
        presentation_json=payload.presentation_json,
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

    if page.entity_type == "project":
        await _require_project_page_access(
            session=session,
            current_user=current_user,
            entity_id=page.entity_id,
            minimum_role=AccessGrantRole.editor,
        )
    elif page.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    await delete_page_layout(session, page)
    return {"message": "Page deleted successfully"}
