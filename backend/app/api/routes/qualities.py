import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Quality,
    QualityCreate,
    QualityPublic,
    QualitiesPublic,
    QualityUpdate,
    Message,
)

router = APIRouter(prefix="/qualities", tags=["qualities"])


@router.get("/", response_model=QualitiesPublic)
def read_qualities(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve qualities.
    """

    count_statement = select(func.count()).select_from(Quality)
    count = session.exec(count_statement).one()
    statement = select(Quality).offset(skip).limit(limit)
    qualities = session.exec(statement).all()

    return QualitiesPublic(data=qualities, count=count)  # type: ignore


@router.get("/{id}", response_model=QualityPublic)
def read_quality(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Quality by ID.
    """
    quality = session.get(Quality, id)
    if not quality:
        raise HTTPException(status_code=404, detail="quality not found")
    return quality


@router.post("/", response_model=QualityPublic)
def create_quality(
    *, session: SessionDep, current_user: CurrentUser, quality_in: QualityCreate
) -> Any:
    """
    Create new quality.
    """
    # Generate quality_name from name
    quality_name = quality_in.name.lower().replace(" ", "_")[:50]

    quality = Quality.model_validate(
        quality_in, update={"enabled": True, "quality_name": quality_name}
    )
    session.add(quality)
    session.commit()
    session.refresh(quality)
    return quality


@router.put("/{id}", response_model=QualityPublic)
def update_quality(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    quality_in: QualityUpdate,
) -> Any:
    """
    Update a quality.
    """
    quality = session.get(Quality, id)
    if not quality:
        raise HTTPException(status_code=404, detail="quality not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = quality_in.model_dump(exclude_unset=True)
    quality.sqlmodel_update(update_dict)
    session.add(quality)
    session.commit()
    session.refresh(quality)
    return quality


@router.delete("/{id}")
def delete_quality(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a quality.
    """
    quality = session.get(Quality, id)
    if not quality:
        raise HTTPException(status_code=404, detail="quality not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(quality)
    session.commit()
    return Message(message="Quality deleted successfully")
