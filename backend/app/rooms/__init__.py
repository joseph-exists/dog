"""
Rooms module for multi-user, multi-agent collaborative chat.

This module contains all room-related models for Phase 1:
- Event sourcing with append-only RoomEvent log
- Transactional projections (Room, RoomParticipant, Message)
- SQLModel-conformant Base/Create/Update/Table/Public/Collection patterns
"""

from app.rooms.room_models import (
    # Message models
    Message,
    MessageBase,
    MessageCreate,
    MessagePublic,
    MessagesPublic,
    MessageUpdate,
    # Room models
    Room,
    RoomBase,
    RoomCreate,
    RoomPublic,
    RoomsPublic,
    RoomUpdate,
    # RoomEvent models (system of record)
    RoomEvent,
    RoomEventBase,
    RoomEventCreate,
    RoomEventPublic,
    RoomEventsPublic,
    # RoomParticipant models
    RoomParticipant,
    RoomParticipantBase,
    RoomParticipantCreate,
    RoomParticipantPublic,
    RoomParticipantsPublic,
    RoomParticipantUpdate,
)

__all__ = [
    # Room models
    "Room",
    "RoomBase",
    "RoomCreate",
    "RoomUpdate",
    "RoomPublic",
    "RoomsPublic",
    # RoomParticipant models
    "RoomParticipant",
    "RoomParticipantBase",
    "RoomParticipantCreate",
    "RoomParticipantUpdate",
    "RoomParticipantPublic",
    "RoomParticipantsPublic",
    # Message models
    "Message",
    "MessageBase",
    "MessageCreate",
    "MessageUpdate",
    "MessagePublic",
    "MessagesPublic",
    # RoomEvent models
    "RoomEvent",
    "RoomEventBase",
    "RoomEventCreate",
    "RoomEventPublic",
    "RoomEventsPublic",
]
