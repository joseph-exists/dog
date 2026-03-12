import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    DiscoveredUserPersonasPublic,
    Message,
    UserPersonaCreate,
    UserPersonaPresentationBase,
    UserPersonaPresentationCreate,
    UserPersonaPresentationPublic,
    UserPersonaPresentationsPublic,
    UserPersonaPresentationUpdate,
    UserPersonaPublic,
    UserPersonasPublic,
    UserPersonaUpdate,
)

router = APIRouter(prefix="/user-personas", tags=["user-personas"])


@router.get("/discoverable", response_model=DiscoveredUserPersonasPublic)
def search_discoverable_user_personas(
    session: SessionDep,
    current_user: CurrentUser,
    q: str,
    limit: int = 20,
    exclude_current_user: bool = True,
) -> Any:
    """
    Search published user personas that are discoverable for collaboration targeting.
    """
    discovered, count = crud.search_discoverable_user_personas(
        session=session,
        query=q,
        actor_user_id=current_user.id,
        limit=min(max(limit, 1), 50),
        exclude_current_user=exclude_current_user,
    )
    return DiscoveredUserPersonasPublic(data=discovered, count=count)


@router.get("/", response_model=UserPersonasPublic)
def read_user_personas(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve user personas for the current user.
    """
    user_personas, count = crud.get_user_personas(
        session=session, user_id=current_user.id, skip=skip, limit=limit
    )
    return UserPersonasPublic(data=user_personas, count=count)


@router.get("/{id}", response_model=UserPersonaPublic)
def read_user_persona(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get user persona by ID.
    """
    user_persona = crud.get_user_persona(
        session=session, id=id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")
    return user_persona


@router.post("/", response_model=UserPersonaPublic)
def create_user_persona(
    *, session: SessionDep, current_user: CurrentUser, user_persona_in: UserPersonaCreate
) -> Any:
    """
    Create new user persona.
    """
    user_persona = crud.create_user_persona(
        session=session, user_persona_in=user_persona_in, user_id=current_user.id
    )
    return user_persona


@router.put("/{id}", response_model=UserPersonaPublic)
def update_user_persona(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    user_persona_in: UserPersonaUpdate,
) -> Any:
    """
    Update a user persona.
    """
    user_persona = crud.get_user_persona(
        session=session, id=id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    user_persona = crud.update_user_persona(
        session=session,
        db_user_persona=user_persona,
        user_persona_in=user_persona_in
    )
    return user_persona


@router.delete("/{id}")
def delete_user_persona(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a user persona.
    """
    user_persona = crud.get_user_persona(
        session=session, id=id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    crud.delete_user_persona(session=session, db_user_persona=user_persona)
    return Message(message="User persona deleted successfully")


@router.get("/{id}/presentations", response_model=UserPersonaPresentationsPublic)
def read_user_persona_presentations(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve audience presentations for a user persona owned by the current user.
    """
    user_persona = crud.get_user_persona(
        session=session,
        id=id,
        user_id=current_user.id,
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    presentations, count = crud.get_user_persona_presentations(
        session=session,
        user_persona_id=id,
        skip=skip,
        limit=limit,
    )
    return UserPersonaPresentationsPublic(data=presentations, count=count)


@router.get(
    "/{id}/presentations/{presentation_id}",
    response_model=UserPersonaPresentationPublic,
)
def read_user_persona_presentation(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    presentation_id: uuid.UUID,
) -> Any:
    """
    Get one audience presentation for a user persona owned by the current user.
    """
    user_persona = crud.get_user_persona(
        session=session,
        id=id,
        user_id=current_user.id,
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    presentation = crud.get_user_persona_presentation(
        session=session,
        id=presentation_id,
        user_persona_id=id,
    )
    if not presentation:
        raise HTTPException(status_code=404, detail="User persona presentation not found")
    return presentation


@router.post(
    "/{id}/presentations",
    response_model=UserPersonaPresentationPublic,
)
def create_user_persona_presentation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    presentation_in: UserPersonaPresentationBase,
) -> Any:
    """
    Create a new audience presentation for a user persona owned by the current user.
    """
    user_persona = crud.get_user_persona(
        session=session,
        id=id,
        user_id=current_user.id,
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    presentation = crud.create_user_persona_presentation(
        session=session,
        user_persona_id=id,
        presentation_in=UserPersonaPresentationCreate(
            user_persona_id=id,
            **presentation_in.model_dump(),
        ),
    )
    return presentation


@router.put(
    "/{id}/presentations/{presentation_id}",
    response_model=UserPersonaPresentationPublic,
)
def update_user_persona_presentation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    presentation_id: uuid.UUID,
    presentation_in: UserPersonaPresentationUpdate,
) -> Any:
    """
    Update an audience presentation for a user persona owned by the current user.
    """
    user_persona = crud.get_user_persona(
        session=session,
        id=id,
        user_id=current_user.id,
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    presentation = crud.get_user_persona_presentation(
        session=session,
        id=presentation_id,
        user_persona_id=id,
    )
    if not presentation:
        raise HTTPException(status_code=404, detail="User persona presentation not found")

    presentation = crud.update_user_persona_presentation(
        session=session,
        db_presentation=presentation,
        presentation_in=presentation_in,
    )
    return presentation


@router.delete("/{id}/presentations/{presentation_id}")
def delete_user_persona_presentation(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    presentation_id: uuid.UUID,
) -> Message:
    """
    Delete an audience presentation for a user persona owned by the current user.
    """
    user_persona = crud.get_user_persona(
        session=session,
        id=id,
        user_id=current_user.id,
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    presentation = crud.get_user_persona_presentation(
        session=session,
        id=presentation_id,
        user_persona_id=id,
    )
    if not presentation:
        raise HTTPException(status_code=404, detail="User persona presentation not found")

    crud.delete_user_persona_presentation(
        session=session,
        db_presentation=presentation,
    )
    return Message(message="User persona presentation deleted successfully")
