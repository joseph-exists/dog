"""
Context Provider Service: Room-aware context builder for agents.

Provides limited context (20 messages + story outline) to prevent
context window overflow while maintaining conversation relevance.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from app.services.logfire_client import ServiceLogfire

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    UserAgentConfig,
    Room,
    RoomMessage,
    RoomParticipant,
    RoomStoryProgress,
    Story,
    StoryNode,
    UserStoryProgress,
)
from app.crud import get_available_choices, get_choice_ancestor_chain_async
from app.services.context_store import ContextItemStore
from app.services.shadow_context_loader import build_shadow_context_items

logger = logging.getLogger(__name__)

SERVICE_ID = "context_provider"
logfire = ServiceLogfire(SERVICE_ID)


@dataclass
class AgentInfo:
    """
    Agent information for agent-aware prompts.

    Agents can see other agents in the room and reference them via @mentions.
    Capabilities enable agent discovery for A2A coordination.
    """

    slug: str
    name: str
    description: str
    participation_mode: str
    capabilities: list[str]


@dataclass
class StoryRuntimeContext:
    """
    Lightweight runtime projection of the room's story state, designed for agent prompts.

    Unlike RoomRuntimePublic (which serves the UI with full model objects), this
    provides text-oriented fields that can be directly formatted into a natural
    language prompt. Agents need to know WHERE the user is in the story, WHAT
    happened so far, and WHAT options are available — not UUIDs or version numbers.

    Attributes:
        current_node_title: Title of the node the user is currently on
        current_node_content: Full text content of the current node
        current_node_type: Node type (e.g., "scene", "dialogue", "choice_point")
        is_end_node: Whether this is a terminal node in the story
        node_chain: Ordered list of node titles representing the path taken
        available_choices: List of choice texts the user can select next
        story_state: Accumulated key-value state from choices made
    """

    current_node_title: str
    current_node_content: str
    current_node_type: str | None
    is_end_node: bool
    node_chain: list[str]  # Breadcrumb trail of node titles (root → current)
    available_choices: list[str]  # Choice texts available from current node
    story_state: dict[str, Any]  # Accumulated state from user's choices


@dataclass
class RoomContext:
    """
    Context object passed to agents for room-aware responses.

    Attributes:
        room_id: UUID of the current room
        story_id: Optional UUID of associated story
        story_data: Story details (title, description) if available
        story_runtime: Live story runtime state (current node, path, choices)
        recent_messages: Last N messages for conversation context
        participants: List of active participants (users and agents)
        room_metadata: Room title, creator, timestamps
        active_agents: List of agents in the room with their details
    """

    room_id: uuid.UUID
    story_id: uuid.UUID | None
    story_data: dict[str, Any] | None
    story_runtime: StoryRuntimeContext | None  # Runtime projection of active story state
    recent_messages: list[dict[str, Any]]
    participants: list[dict[str, Any]]
    room_metadata: dict[str, Any]
    active_agents: list[AgentInfo]
    extra_contexts: list[dict[str, Any]]


async def build_room_context(
    *,
    room_id: uuid.UUID,
    session: AsyncSession,
    message_limit: int = 20,
    agent_slug: str | None = None,
    context_store: ContextItemStore | None = None,
) -> RoomContext:
    """
    Build context for an agent given a room_id.

    This function:
    1. Loads room metadata (title, story_id, etc.)
    2. Loads associated story data if present
    3. Fetches last N messages for conversation context
    4. Lists active participants

    Args:
        room_id: UUID of the room
        session: Async database session
        message_limit: Max messages to include (default 20)

    Returns:
        RoomContext with all data needed for agent response

    Raises:
        ValueError: If room does not exist
    """
    span_tags: dict[str, Any] = {
        "room_id": str(room_id),
        "message_limit": message_limit,
    }
    if agent_slug:
        span_tags["agent_slug"] = agent_slug

    with logfire.span("agent.build_room_context", **span_tags):
        # Load room
        result = await session.exec(select(Room).where(Room.room_id == room_id))
        room_row = result.one_or_none()
        room = room_row[0] if room_row and not isinstance(room_row, Room) else room_row
        if not room:
            raise ValueError(f"Room {room_id} not found")

        # Load story data if associated
        story_data = None
        if room.story_id:
            story_result = await session.exec(
                select(Story).where(Story.id == room.story_id)
            )
            story_row = story_result.one_or_none()
            story = (
                story_row[0]
                if story_row and not isinstance(story_row, Story)
                else story_row
            )
            if story:
                story_data = {
                    "id": str(story.id),
                    "title": story.title,
                    "description": story.description,
                    "is_published": story.is_published,
                }

        # --- Story Runtime Projection ---
        # Bridges Surface 1 (Room Runtime API) into the agent context.
        # Agents need to know the user's current position in the story, the path
        # they've taken, and what choices are available — so they can respond
        # appropriately to the narrative state.
        story_runtime: StoryRuntimeContext | None = None
        if room.story_id:
            try:
                # Step 1: Find the room's shared story progress record
                rsp_result = await session.exec(
                    select(RoomStoryProgress).where(RoomStoryProgress.room_id == room_id)
                )
                rsp_row = rsp_result.one_or_none()
                room_story_progress = (
                    rsp_row[0]
                    if rsp_row and not isinstance(rsp_row, RoomStoryProgress)
                    else rsp_row
                )

                if room_story_progress:
                    # Step 2: Load the canonical UserStoryProgress (the actual state)
                    progress_result = await session.exec(
                        select(UserStoryProgress).where(
                            UserStoryProgress.id == room_story_progress.active_progress_id
                        )
                    )
                    progress_row = progress_result.one_or_none()
                    progress = (
                        progress_row[0]
                        if progress_row and not isinstance(progress_row, UserStoryProgress)
                        else progress_row
                    )

                    if progress and progress.current_node_id is not None:
                        # Step 3: Load the current node the user is on
                        current_node_obj = await session.get(StoryNode, progress.current_node_id)

                        if current_node_obj:
                            # Step 4: Get available choices from this node,
                            # filtered by current story_state (conditional branches)
                            choices = await get_available_choices(
                                session=session,
                                node_id=progress.current_node_id,
                                story_state=progress.story_state or {},
                            )
                            choice_texts = [c.text for c in choices]

                            # Step 5: Build node chain (the breadcrumb trail of the path taken)
                            # Uses the choice ancestor chain to reconstruct traversal order
                            node_chain_titles: list[str] = []
                            if progress.head_choice_id:
                                chain = await get_choice_ancestor_chain_async(
                                    session=session,
                                    choice_id=progress.head_choice_id,
                                )
                                if chain:
                                    # Collect node IDs in traversal order: first from_node, then all to_nodes
                                    chain_node_ids = [chain[0].from_node_id] + [
                                        c.to_node_id for c in chain
                                    ]
                                    # Batch-load all nodes in the chain
                                    chain_nodes_result = await session.exec(
                                        select(StoryNode).where(
                                            StoryNode.id.in_([str(nid) for nid in chain_node_ids])
                                        )
                                    )
                                    chain_nodes = chain_nodes_result.all()
                                    nodes_by_id = {n.id: n for n in chain_nodes}
                                    node_chain_titles = [
                                        nodes_by_id[nid].title
                                        for nid in chain_node_ids
                                        if nid in nodes_by_id
                                    ]

                            story_runtime = StoryRuntimeContext(
                                current_node_title=current_node_obj.title,
                                current_node_content=current_node_obj.content or "",
                                current_node_type=current_node_obj.node_type,
                                is_end_node=current_node_obj.is_end_node,
                                node_chain=node_chain_titles,
                                available_choices=choice_texts,
                                story_state=progress.story_state or {},
                            )
            except Exception as exc:
                # Non-fatal: if runtime loading fails, agent still gets basic context
                logger.warning(
                    f"Failed to load story runtime for room {room_id}: {exc}"
                )

        # Load recent messages (ordered by created_at desc, then reversed)
        messages_result = await session.exec(
            select(RoomMessage)
            .where(
                RoomMessage.room_id == room_id,
                RoomMessage.active_for_context == True,  # noqa: E712
            )
            .order_by(RoomMessage.created_at.desc())
            .limit(message_limit)
        )
        messages = messages_result.all()

        recent_messages = [
            {
                "message_id": str(msg.message_id),
                "sender_type": msg.sender_type,
                "sender_id": str(msg.sender_id) if msg.sender_id else None,
                "agent_name": msg.agent_name,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in reversed(messages)  # Chronological order
        ]

        # Load active participants
        participants_result = await session.exec(
            select(RoomParticipant).where(
                RoomParticipant.room_id == room_id,
                RoomParticipant.active == True,  # noqa: E712
            )
        )
        participants_list = participants_result.all()

        participants = [
            {
                "participant_id": p.participant_id,
                "participant_type": p.participant_type,
                "role": p.role,
                "joined_at": p.joined_at.isoformat(),
            }
            for p in participants_list
        ]

        # Fetch agent details for agent participants
        active_agents: list[AgentInfo] = []
        for p in participants_list:
            if p.participant_type == "agent":
                # participant_id is UserAgentConfig.slug (preferred) with legacy UUID support.
                agent_config = None

                agent_result = await session.exec(
                    select(UserAgentConfig).where(UserAgentConfig.slug == p.participant_id)
                )
                agent_config_row = agent_result.one_or_none()
                agent_config = (
                    agent_config_row[0]
                    if agent_config_row and not isinstance(agent_config_row, UserAgentConfig)
                    else agent_config_row
                )

                if not agent_config:
                    try:
                        agent_uuid = uuid.UUID(p.participant_id)
                        agent_config = await session.get(UserAgentConfig, agent_uuid)
                    except ValueError:
                        agent_config = None

                if agent_config and agent_config.is_enabled:
                    active_agents.append(
                        AgentInfo(
                            slug=agent_config.slug,
                            name=agent_config.name,
                            description=agent_config.description or "",
                            participation_mode=agent_config.participation_mode or "on_mention",
                            capabilities=agent_config.capabilities or [],
                        )
                    )

        room_metadata = {
            "room_id": str(room.room_id),
            "title": room.title,
            "creator_id": str(room.creator_id),
            "created_at": room.created_at.isoformat(),
            "last_activity": room.last_activity.isoformat(),
        }

        extra_contexts: list[dict[str, Any]] = []
        if context_store:
            try:
                shadow_items = await build_shadow_context_items(
                    room_id=room_id,
                    agent_slug=agent_slug,
                    session=session,
                )
                for item in shadow_items:
                    await context_store.add(item)
            except Exception as exc:
                logger.warning(
                    f"Failed to build Shadow context items for room {room_id} (agent_slug={agent_slug}): {exc}"
                )

            items = await context_store.list(room_id=room_id, agent_slug=agent_slug)
            source_priority = {"seed": 0, "backend": 1, "frontend": 2}
            items_sorted = sorted(
                items,
                key=lambda item: (source_priority.get(item.source, 99), item.created_at),
            )
            extra_contexts = [
                {
                    "context_type": item.context_type,
                    "payload": item.payload,
                    "source": item.source,
                }
                for item in items_sorted
            ]

        context = RoomContext(
            room_id=room_id,
            story_id=room.story_id,
            story_data=story_data,
            story_runtime=story_runtime,  # Runtime projection of active story state
            recent_messages=recent_messages,
            participants=participants,
            room_metadata=room_metadata,
            active_agents=active_agents,
            extra_contexts=extra_contexts,
        )

        logfire.info(
            "agent.build_room_context_completed",
            **span_tags,
            recent_messages=len(recent_messages),
            participant_count=len(participants),
            active_agents=len(active_agents),
        )
        return context
