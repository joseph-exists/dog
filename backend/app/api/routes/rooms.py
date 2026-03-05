"""
Room API Routes (Phase 1)

This module implements the REST API endpoints for multi-user, multi-agent
collaborative chat rooms following the Phase 1 Plan requirements.

All endpoints use async for I/O operations and enforce room-based authorization
via active membership in RoomParticipant.

Architecture:
- All writes go through event_emitter.emit_event()
- Authorization enforced at CRUD level
- Supports both user and agent participants as first-class entities

NOTE: agent participants are addressed by `AgentConfig.slug` (not display name).
"""

from datetime import datetime
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud import (
    add_participant,
    change_participant_role,
    check_can_delete_message,
    check_can_edit_message,
    check_can_pin_message,
    check_room_membership,
    create_room,
    delete_message,
    edit_message,
    get_room_for_user,
    list_room_messages,
    list_rooms_for_user,
    pin_message,
    remove_participant,
    send_user_message,
    toggle_message_context,
    unpin_message,
    update_room_metadata,
)
from app.models import (
    MessageContextToggle,
    MessageEdit,
    MessageResponse,
    ParticipantAddRequest,
    ParticipantRoleChangeRequest,
    Room,
    RoomCreate,
    RoomMessage,
    RoomMessagePublic,
    RoomMessageSend,
    RoomMessagesPublic,
    RoomParticipant,
    RoomParticipantPublic,
    RoomParticipantsPublic,
    RoomPublic,
    RoomsPublic,
    RoomUpdate,
    RepoRoomEventRequest,
    UIActionRequest,
)
from app.services.agent_runner import invoke_agent_manually, run_agents_for_message
from app.services.event_emitter import emit_event

router = APIRouter(prefix="/rooms", tags=["rooms"])
logger = logging.getLogger(__name__)


# ============================================================================
# Room Endpoints
# ============================================================================


@router.post("/", response_model=RoomPublic)
async def create_new_room(
    *,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    room_in: RoomCreate,
) -> Any:
    """
    Create a new room.

    The current user becomes the room owner. Optionally associate with a story.

    Transaction is automatically managed:
    - Commits on successful completion
    - Rolls back on any exception

    Event flow:
    1. Emits room.created event
    2. Emits participant.joined event for creator (as owner)
    3. Returns room projection
    """
    room = await create_room(
        creator_id=current_user.id,
        story_id=room_in.story_id,
        title=room_in.title,
        session=session,
    )
    return room


@router.get("/", response_model=RoomsPublic)
async def list_user_rooms(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List all rooms where the current user is an active participant.

    Returns rooms ordered by last_activity (most recent first).
    """
    rooms = await list_rooms_for_user(
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=limit,
    )
    return rooms


@router.get("/{room_id}", response_model=RoomPublic)
async def get_room(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get room details by ID.

    Only accessible to active participants.
    """
    room = await get_room_for_user(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )
    return room


@router.patch("/{room_id}", response_model=RoomPublic)
async def update_room(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    room_in: RoomUpdate,
) -> Any:
    """
    Update room metadata (owner-only).

    Transaction automatically managed. Emits room.updated event with changed fields.
    """
    room = await update_room_metadata(
        room_id=room_id,
        user_id=current_user.id,
        title=room_in.title,
        session=session,
    )
    return room


@router.delete("/{room_id}", response_model=MessageResponse)
async def delete_room(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Soft-delete a room (owner-only).

    Sets deleted_at timestamp. Room and all child data (messages, events,
    participants) remain in the database but are hidden from queries.
    """
    room = await session.get(Room, room_id)
    if not room or room.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only room owner can delete")
    room.deleted_at = datetime.utcnow()
    session.add(room)
    return MessageResponse(message="Room deleted successfully")


# ============================================================================
# Participant Endpoints
# ============================================================================


@router.post("/{room_id}/participants", response_model=RoomParticipantPublic)
async def add_room_participant(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    participant_in: ParticipantAddRequest,
) -> Any:
    """
    Add a participant to a room (owner-only).

    Transaction automatically managed. Supports adding both users and agents.
    Operation is idempotent: re-adding an inactive participant will reactivate them.

    Event flow:
    1. Verifies current user is room owner
    2. Emits participant.joined event
    3. Returns participant projection

    Args:
        participant_id: UUID string for users, agent name for agents
        participant_type: "user" or "agent"
        role: "owner" or "member" (default: "member")
    """
    participant = await add_participant(
        room_id=room_id,
        user_id=current_user.id,
        participant_id=participant_in.participant_id,
        participant_type=participant_in.participant_type,
        role=participant_in.role,
        session=session,
    )
    return participant

@router.get("/story/{story_id}", response_model=RoomsPublic)
async def get_rooms_for_story(
    story_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 10,
) -> Any:
    """Get rooms for a story where user is creator or active participant."""
    from app.crud import list_rooms_for_story

    rooms = await list_rooms_for_story(
        story_id=story_id,
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=limit,
    )
    return rooms

@router.get("/{room_id}/participants", response_model=RoomParticipantsPublic)
async def list_room_participants(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    include_inactive: bool = False,
) -> Any:
    """
    List participants in a room.

    Only accessible to room participants. Returns both users and agents.
    By default only active participants are returned. Set include_inactive=true
    to also return deactivated participants (useful for toggle UI).
    """
    from sqlmodel import select

    # Check membership first
    from app.crud import check_room_membership

    if not await check_room_membership(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    # Query participants (optionally include inactive)
    query = select(RoomParticipant).where(RoomParticipant.room_id == room_id)
    if not include_inactive:
        query = query.where(RoomParticipant.active)
    result = await session.exec(query)
    participants = result.all()

    return RoomParticipantsPublic(
        data=[RoomParticipantPublic.model_validate(p) for p in participants],
        count=len(participants),
    )


@router.delete("/{room_id}/participants/{participant_id}")
async def remove_room_participant(
    *,
    room_id: UUID,
    participant_id: str,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> MessageResponse:
    """
    Remove a participant from a room (owner-only, soft delete).

    Transaction automatically managed. Emits participant.left event which sets active=False.
    Historical events are preserved.

    Args:
        participant_id: UUID string for users, agent name for agents
    """
    await remove_participant(
        room_id=room_id,
        user_id=current_user.id,
        participant_id=participant_id,
        session=session,
    )
    return MessageResponse(message="Participant removed successfully")


@router.patch(
    "/{room_id}/participants/{participant_id}/role",
    response_model=RoomParticipantPublic,
)
async def change_room_participant_role(
    *,
    room_id: UUID,
    participant_id: str,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    role_in: ParticipantRoleChangeRequest,
) -> Any:
    """
    Change a participant's role (owner-only).

    Transaction automatically managed. Emits participant.role_changed event.

    Args:
        participant_id: UUID string for users, agent name for agents
        new_role: "owner" or "member"
    """
    participant = await change_participant_role(
        room_id=room_id,
        user_id=current_user.id,
        participant_id=participant_id,
        new_role=role_in.new_role,
        session=session,
    )
    return participant


# ============================================================================
# Message Endpoints
# ============================================================================


@router.post("/{room_id}/messages", response_model=RoomMessagePublic)
async def send_message(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    message_in: RoomMessageSend,
) -> Any:
    """
    Send a message to a room.

    After user message is persisted, triggers any active agents in the room.
    All operations (user message + agent responses) are atomic within one transaction.

    Transaction automatically managed. Emits message.user event, then triggers agents.
    Only accessible to active participants.
    """
    # 1. Send user message
    room_message = await send_user_message(
        room_id=room_id,
        user_id=current_user.id,
        content=message_in.content,
        session=session,
    )

    # 2. Trigger agents (within same transaction)
    # Pass user_id so agents can use the user's API credentials
    try:
        await run_agents_for_message(
            room_id=room_id,
            trigger_message=message_in.content,
            session=session,
            user_id=current_user.id,
        )
    except Exception:
        logger.exception(
            "run_agents_for_message failed; user message committed",
            extra={"room_id": str(room_id), "user_id": str(current_user.id)},
        )

    # 3. Transaction commits here (on return)
    return room_message


@router.get("/{room_id}/messages", response_model=RoomMessagesPublic)
async def list_messages(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    limit: int = Query(default=50, le=100),
    before: datetime | None = Query(default=None),
    active_for_context: bool | None = None,  # None = both, True = active only, False = inactive only
    is_pinned: bool | None = None,           # None = both, True = pinned only, False = unpinned only
    sender_type: str | None = None,          # "user" | "agent" | "agent_internal" | None
    include_internal: bool = Query(default=False),
    sender_id: UUID | None = None,           # Specific user/agent
) -> Any:
    """
    List messages in a room with cursor-based pagination and optional filters.
    All filters applied server-side.
    Only accessible to active participants.

    Args:
        limit: Maximum number of messages to return (max 100)
        before: Cursor timestamp - returns messages before this time
    """
    try:
        room_messages = await list_room_messages(
            room_id=room_id,
            user_id=current_user.id,
            active_for_context=active_for_context,
            is_pinned=is_pinned,
            sender_type=sender_type,
            sender_id=sender_id,
            include_internal=include_internal,
            limit=limit,
            before=before,
            session=session,
        )
    except Exception:
        logger.exception(
            "list_messages failed",
            extra={
                "room_id": str(room_id),
                "user_id": str(current_user.id),
                "limit": limit,
                "before": str(before) if before else None,
                "include_internal": include_internal,
            },
        )
        raise

    logger.info(
        "list_messages success",
        extra={
            "room_id": str(room_id),
            "user_id": str(current_user.id),
            "count": room_messages.count,
            "size": len(room_messages.data),
        },
    )
    return room_messages


# ============================================================================
# Message Management Endpoints (Phase 5)
# ============================================================================


@router.patch("/{room_id}/messages/{message_id}", response_model=RoomMessagePublic)
async def edit_message_endpoint(
    *,
    room_id: UUID,
    message_id: UUID,
    message_update: MessageEdit,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Edit message content.

    Authorization:
    - User messages: Message author OR room owner can edit
    - Agent messages: Owner only can edit

    Does NOT change active_for_context status.
    Transaction automatically managed. Emits message.edited event.
    """
    # Check authorization
    can_edit = await check_can_edit_message(
        room_id=room_id,
        message_id=message_id,
        user_id=current_user.id,
        session=session,
    )
    if not can_edit:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to edit this message"
        )

    # Edit message
    message = await edit_message(
        room_id=room_id,
        message_id=message_id,
        user_id=current_user.id,
        new_content=message_update.content,
        session=session,
    )
    return message


@router.post("/{room_id}/messages/{message_id}/pin", response_model=RoomMessagePublic)
async def pin_message_endpoint(
    *,
    room_id: UUID,
    message_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Pin message and auto-mark as active for context.

    Authorization: Room owner only.
    Transaction automatically managed. Emits message.pinned event.
    """
    # Check authorization
    can_pin = await check_can_pin_message(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )
    if not can_pin:
        raise HTTPException(
            status_code=403,
            detail="Only room owners can pin messages"
        )

    # Pin message
    message = await pin_message(
        room_id=room_id,
        message_id=message_id,
        user_id=current_user.id,
        session=session,
    )
    return message


@router.delete("/{room_id}/messages/{message_id}/pin", response_model=RoomMessagePublic)
async def unpin_message_endpoint(
    *,
    room_id: UUID,
    message_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Unpin message. Does NOT change active_for_context status.

    Authorization: Room owner only.
    Transaction automatically managed. Emits message.unpinned event.
    """
    # Check authorization
    can_pin = await check_can_pin_message(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )
    if not can_pin:
        raise HTTPException(
            status_code=403,
            detail="Only room owners can unpin messages"
        )

    # Unpin message
    message = await unpin_message(
        room_id=room_id,
        message_id=message_id,
        session=session,
    )
    return message


@router.patch("/{room_id}/messages/{message_id}/context", response_model=RoomMessagePublic)
async def toggle_message_context_endpoint(
    *,
    room_id: UUID,
    message_id: UUID,
    context_update: MessageContextToggle,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Toggle message active_for_context status.

    Authorization: Any active participant can toggle.
    Transaction automatically managed. Emits message.context_toggled event.
    """
    # Check membership
    is_member = await check_room_membership(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )
    if not is_member:
        raise HTTPException(status_code=403, detail="Access denied")

    # Toggle context
    message = await toggle_message_context(
        room_id=room_id,
        message_id=message_id,
        active_for_context=context_update.active_for_context,
        session=session,
    )
    return message


@router.delete("/{room_id}/messages/{message_id}", status_code=204)
async def delete_message_endpoint(
    *,
    room_id: UUID,
    message_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> None:
    """
    Delete a message (soft delete via event).

    Authorization: Room owner only.
    Transaction automatically managed. Emits message.deleted event.
    Historical event is preserved.
    """
    # Check authorization
    can_delete = await check_can_delete_message(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )
    if not can_delete:
        raise HTTPException(
            status_code=403,
            detail="Only room owners can delete messages"
        )

    # Delete message
    await delete_message(
        room_id=room_id,
        message_id=message_id,
        user_id=current_user.id,
        session=session,
    )


# ============================================================================
# AG-UI Actions
# ============================================================================


@router.post("/{room_id}/ui-action")
async def handle_ui_action(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    action_in: UIActionRequest,
) -> Any:
    """
    Handle a UI action button click from the frontend.

    When an agent emits action_buttons via emit_ui_component(), each button has
    an `action` string (e.g., "expand_section", "regenerate"). When the user
    clicks one, the frontend sends it here.

    This endpoint:
    1. Looks up the source message to identify which agent emitted the component
    2. Invokes that specific agent with the action as trigger context
    3. The agent processes the action and responds (new message in the room)

    Unlike regular messages, this:
    - Does NOT create a user-visible message in the chat history
    - Targets only the originating agent (not all agents in the room)
    - Bypasses participation mode checks (the agent is invoked directly)

    Authorization: Must be an active participant in the room.
    """
    # Verify the user is a participant in this room
    await check_room_membership(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )

    # Look up the source message to find which agent emitted the action button.
    # The source_message_id identifies the agent message containing the UI component.
    source_msg = await session.get(RoomMessage, action_in.source_message_id)
    if not source_msg:
        raise HTTPException(
            status_code=404,
            detail="Source message not found",
        )

    # Only agent messages can have UI components — reject if it's a user message
    if source_msg.sender_type != "agent":
        raise HTTPException(
            status_code=400,
            detail="Source message is not from an agent",
        )

    # The agent_name on the message is the agent's slug (unique identifier).
    # This is what invoke_agent_manually uses to resolve and run the agent.
    agent_slug = source_msg.agent_name
    if not agent_slug:
        raise HTTPException(
            status_code=400,
            detail="Source message has no agent identifier",
        )

    # Construct the trigger message the agent will receive.
    # Format: "[UI Action: action_string]" — agents can parse this to understand
    # the user clicked an action button and respond appropriately.
    trigger_message = f"[UI Action: {action_in.action}]"

    logger.info(
        "AG-UI action: user=%s agent=%s action=%s component=%s",
        current_user.id,
        agent_slug,
        action_in.action,
        action_in.component_id,
    )

    # Invoke the originating agent directly, bypassing participation mode.
    # This runs the agent with the action as context; the agent's response
    # will be emitted as a new message in the room (visible to all participants).
    await invoke_agent_manually(
        room_id=room_id,
        agent_slug=agent_slug,
        trigger_message=trigger_message,
        session=session,
        user_id=current_user.id,
    )

    # Return 200 with status. The agent's response arrives asynchronously
    # via the normal message stream (WebSocket or polling).
    return {"status": "accepted", "agent": agent_slug, "action": action_in.action}


@router.post("/{room_id}/repo-event")
async def emit_repo_room_event(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    event_in: RepoRoomEventRequest,
) -> Any:
    """
    Emit a room-scoped repository collaboration event.

    Used by room-embedded repo panels to publish structured actions for:
    - selection changes
    - file opens
    - ref observations/changes

    Authorization: Any active room participant can emit events.
    """
    await check_room_membership(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )

    action_to_event_type = {
        "selection": "room.repo.selection",
        "open": "room.repo.opened",
        "ref": "room.repo.ref_changed",
    }
    event_type = action_to_event_type[event_in.action]

    event_payload = {
        "actor_user_id": str(current_user.id),
        "action": event_in.action,
        "panel_id": event_in.panel_id,
        "selection_key": event_in.selection_key,
        "path": event_in.path,
        "ref": event_in.ref,
        "repo_id": str(event_in.repo_id) if event_in.repo_id else None,
        "metadata": event_in.metadata or {},
    }

    event = await emit_event(
        session=session,
        room_id=room_id,
        event_type=event_type,
        payload=event_payload,
    )

    return {
        "status": "accepted",
        "event_type": event_type,
        "sequence": event.room_sequence,
    }
