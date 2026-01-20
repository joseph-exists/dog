import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.services.shadow_exporters import build_persona_snapshot
from app.services.shadow_service import shadow_service
from app.models import (
    Persona,
    Event,
    PersonaQualityLink,
    Message,
)
from app import crud

router = APIRouter(prefix="/personas/{persona_id}/events", tags=["persona-events"])


@router.post("/{event_id}", response_model=Message)
def process_persona_event(
    session: SessionDep,
    current_user: CurrentUser,
    persona_id: uuid.UUID,
    event_id: uuid.UUID
) -> Any:
    """
    Process an event for a persona, which may trigger quality state changes.
    """
    # Verify the persona exists
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Verify the event exists
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    try:
        affected_links = crud.process_persona_event(
            session=session,
            persona_id=persona_id,
            event_id=event_id
        )

        try:
            snapshot = build_persona_snapshot(session=session, persona_id=persona_id)
            shadow_service.enqueue_entity_version(
                session=session,
                user=current_user,
                entity_type="persona",
                entity_id=persona_id,
                entity_data=snapshot,
                message=f"Persona event processed: {event_id}",
            )
        except Exception:
            pass

        if affected_links:
            return Message(message=f"Event processed successfully. {len(affected_links)} qualities affected.")
        else:
            return Message(message="Event processed successfully. No qualities were affected.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
