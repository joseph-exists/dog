import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Event,
    EventCreate,
    EventPublic,
    EventsPublic,
    EventUpdate,
    Message,
)
from app import crud

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=EventsPublic)
def read_events(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve events.
    """
    count_statement = select(func.count()).select_from(Event)
    count = session.exec(count_statement).one()
    statement = select(Event).offset(skip).limit(limit)
    events = session.exec(statement).all()

    return EventsPublic(data=events, count=count)


@router.get("/{id}", response_model=EventPublic)
def read_event(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get Event by ID.
    """
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/", response_model=EventPublic)
def create_event(
    *, session: SessionDep, current_user: CurrentUser, event_in: EventCreate
) -> Any:
    """
    Create new event.
    """
    event = crud.create_event(session=session, event_in=event_in)
    return event


@router.put("/{id}", response_model=EventPublic)
def update_event(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    event_in: EventUpdate,
) -> Any:
    """
    Update an event.
    """
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = event_in.model_dump(exclude_unset=True)
    event.sqlmodel_update(update_dict)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


@router.delete("/{id}")
def delete_event(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an event.
    """
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(event)
    session.commit()
    return Message(message="Event deleted successfully")
