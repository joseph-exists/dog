from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query, status

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    SvgAssetCreate,
    SvgAssetPublic,
    SvgAssetsPublic,
    SvgAssetUpdate,
    SvgAssetVisibility,
)

router = APIRouter(prefix="/svgs", tags=["svgs"])


def _require_svg_asset_owned(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    svg_id: uuid.UUID,
):
    asset = crud.get_svg_asset(session=session, id=svg_id, owner_id=current_user.id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SVG asset not found")
    return asset


@router.get("/", response_model=SvgAssetsPublic)
def list_svgs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    visibility: Annotated[SvgAssetVisibility | None, Query()] = None,
) -> Any:
    """List current user's SVG assets with optional visibility filtering."""
    assets, count = crud.get_svg_assets(
        session=session,
        owner_id=current_user.id,
        visibility=visibility,
        skip=skip,
        limit=limit,
    )
    return SvgAssetsPublic(data=assets, count=count)


@router.get("/{svg_id}", response_model=SvgAssetPublic)
def get_svg(
    session: SessionDep,
    current_user: CurrentUser,
    svg_id: Annotated[uuid.UUID, Path()],
) -> Any:
    """Get one SVG asset owned by the current user."""
    return _require_svg_asset_owned(
        session=session,
        current_user=current_user,
        svg_id=svg_id,
    )


@router.post(
    "/",
    response_model=SvgAssetPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_svg(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    svg_in: SvgAssetCreate,
) -> Any:
    """Create a private SVG or create a public copy from a private source."""
    return crud.create_svg_asset(
        session=session,
        owner_id=current_user.id,
        svg_asset_in=svg_in,
    )


@router.patch("/{svg_id}", response_model=SvgAssetPublic)
def patch_svg(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    svg_id: Annotated[uuid.UUID, Path()],
    svg_in: SvgAssetUpdate,
) -> Any:
    """Patch an SVG asset owned by the current user."""
    asset = _require_svg_asset_owned(
        session=session,
        current_user=current_user,
        svg_id=svg_id,
    )
    return crud.update_svg_asset(
        session=session,
        db_svg_asset=asset,
        svg_asset_in=svg_in,
    )


@router.delete("/{svg_id}", response_model=Message)
def delete_svg(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    svg_id: Annotated[uuid.UUID, Path()],
) -> Any:
    """Delete an SVG asset owned by the current user."""
    asset = _require_svg_asset_owned(
        session=session,
        current_user=current_user,
        svg_id=svg_id,
    )
    crud.delete_svg_asset(session=session, db_svg_asset=asset)
    return Message(message="SVG asset deleted successfully")

