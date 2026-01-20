from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud import list_room_participant_bindings, set_participant_binding
from app.models import (
    ParticipantBindingChangeRequest,
    RoomParticipantBindingPublic,
    RoomParticipantBindingsPublic,
)
from app.services.shadow_tasks import shadow_room_version_best_effort

router = APIRouter(prefix="/rooms", tags=["room-participant-bindings"])


@router.get("/{room_id}/bindings", response_model=RoomParticipantBindingsPublic)
async def read_room_bindings(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    include_history: bool = Query(default=False),
) -> Any:
    """
    List active (or historical) runtime bindings for room participants.

    Authorization: active room membership required.
    """
    return await list_room_participant_bindings(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
        include_history=include_history,
    )


@router.put(
    "/{room_id}/participants/{participant_id}/binding",
    response_model=RoomParticipantBindingPublic,
)
async def put_participant_binding(
    *,
    room_id: UUID,
    participant_id: str,
    binding_in: ParticipantBindingChangeRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Set a participant's active binding (persona + model/provider) in a room.

    This emits participant.binding_changed and updates projections transactionally.
    """
    try:
        binding = await set_participant_binding(
            room_id=room_id,
            acting_user=current_user,
            participant_type=binding_in.participant_type,
            participant_id=participant_id,
            persona_id=binding_in.persona_id,
            model_name=binding_in.model_name,
            user_llm_provider_id=binding_in.user_llm_provider_id,
            session=session,
        )

        # Post-commit, best-effort room Shadow version write (Task 5/6).
        background_tasks.add_task(
            shadow_room_version_best_effort,
            room_id=room_id,
            actor_user_id=current_user.id,
            message=f"Binding change: {binding_in.participant_type}:{participant_id}",
        )
        return binding
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
