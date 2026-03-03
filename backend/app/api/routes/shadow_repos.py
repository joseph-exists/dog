from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.models import ShadowRepoFileContent, ShadowRepoViewResponse
from app.services.shadow_repo_view_service import (
    ShadowRepoViewNotFound,
    shadow_repo_view_service,
)

router = APIRouter(prefix="/shadow-repos", tags=["shadow-repos"])


def _authorize_shadow_repo_or_404(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    entity_type: str,
    entity_id: uuid.UUID,
) -> None:
    try:
        shadow_repo_view_service.authorize_shadow_repo_read(
            session=session,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    except ShadowRepoViewNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shadow repo not found",
        ) from exc


@router.get("/{entity_type}/{entity_id}/view", response_model=ShadowRepoViewResponse)
def get_shadow_repo_view(
    entity_type: str,
    entity_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    path: str = Query(default=""),
    commit_limit: int = Query(default=10, ge=1, le=100),
) -> ShadowRepoViewResponse:
    _authorize_shadow_repo_or_404(
        session=session,
        current_user=current_user,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    try:
        return shadow_repo_view_service.get_repo_view(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
            path=path,
            commit_limit=commit_limit,
        )
    except ShadowRepoViewNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shadow repo not found",
        ) from exc


@router.get("/{entity_type}/{entity_id}/file", response_model=ShadowRepoFileContent)
def get_shadow_repo_file(
    entity_type: str,
    entity_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    path: str = Query(..., min_length=1),
) -> ShadowRepoFileContent:
    _authorize_shadow_repo_or_404(
        session=session,
        current_user=current_user,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    try:
        return shadow_repo_view_service.get_file_content(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
            path=path,
        )
    except ShadowRepoViewNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shadow repo not found",
        ) from exc
