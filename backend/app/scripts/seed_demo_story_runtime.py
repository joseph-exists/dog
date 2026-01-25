"""
Seed script for the Story Runtime Demo.

Creates all database entities needed for "The Enchanted Library" demo:
- Story with 5 nodes (branching narrative)
- Node choices with state management
- Story state variables
- Room with agents and participants
- Persona + UserPersona for the first superuser
- UserStoryProgress and RoomStoryProgress initialization

Run via: cd backend && python -m app.scripts.seed_demo_story_runtime
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

from sqlmodel import select

from app.core.config import settings
from app.core.db import async_session_maker
from app.models import (
    AgentConfig,
    NodeChoice,
    Persona,
    Room,
    RoomParticipant,
    RoomStoryProgress,
    StateValueType,
    Story,
    StoryNode,
    StoryStateVariable,
    User,
    UserPersona,
    UserStoryProgress,
)

DEMO_ROOM_ID = uuid.UUID | None


async def seed() -> None:
    async with async_session_maker() as session:
        # Idempotency check: skip if demo room already exists
        existing_room = await session.exec(
            select(Room).where(Room.title == "Story Runtime Demo Room")
        )
        if existing_room.first() is not None:
            print("Demo room already exists. Skipping seed.")
            print(f"Room UUID: {DEMO_ROOM_ID}")
            return

        # Find the first superuser
        result = await session.exec(
            select(User).where(User.email == settings.FIRST_SUPERUSER)
        )
        superuser = result.first()
        if superuser is None:
            print("ERROR: First superuser not found. Run init_db first.")
            return

        owner_id = superuser.id
        now = datetime.utcnow()

        # 1. Create the Story
        story = Story(
            id=DEMO_STORY_ID,
            owner_id=owner_id,
            title="The Enchanted Library",
            description="A short branching narrative with 5 nodes exploring a magical library.",
            current_version=1,
            published_version=1,
            is_published=True,
            created_at=now,
            updated_at=now,
        )
        session.add(story)

        # 2. Create Story Nodes (version 1)
        node_1 = StoryNode(
            id=DEMO_NODE_1_ID,
            story_id=DEMO_STORY_ID,
            story_version=1,
            title="The Library Entrance",
            content=(
                "You stand before an ancient library. The heavy oak doors creak open, "
                "revealing dusty shelves stretching into darkness. A faint glow emanates "
                "from somewhere deep within."
            ),
            is_start_node=True,
            is_end_node=False,
            created_at=now,
            updated_at=now,
        )
        node_2 = StoryNode(
            id=DEMO_NODE_2_ID,
            story_id=DEMO_STORY_ID,
            story_version=1,
            title="The Reading Room",
            content=(
                "Rows of leather-bound books line the walls. A large tome sits open on a "
                "central pedestal, its pages glowing with soft golden light. A brass key "
                "hangs from a hook near the window."
            ),
            is_start_node=False,
            is_end_node=False,
            created_at=now,
            updated_at=now,
        )
        node_3 = StoryNode(
            id=DEMO_NODE_3_ID,
            story_id=DEMO_STORY_ID,
            story_version=1,
            title="The Restricted Section",
            content=(
                "Behind a velvet rope, towering shelves hold books bound in strange materials. "
                "The air hums with latent energy. A spectral librarian materializes, watching "
                "you carefully."
            ),
            is_start_node=False,
            is_end_node=False,
            created_at=now,
            updated_at=now,
        )
        node_4 = StoryNode(
            id=DEMO_NODE_4_ID,
            story_id=DEMO_STORY_ID,
            story_version=1,
            title="The Secret Chamber",
            content=(
                "The brass key turns smoothly in the hidden lock. The wall slides open to "
                "reveal a small chamber filled with floating orbs of light. Each orb contains "
                "a swirling memory."
            ),
            is_start_node=False,
            is_end_node=False,
            created_at=now,
            updated_at=now,
        )
        node_5 = StoryNode(
            id=DEMO_NODE_5_ID,
            story_id=DEMO_STORY_ID,
            story_version=1,
            title="The Library's Heart",
            content=(
                "You've discovered the library's deepest secret -- a living book that writes "
                "itself, recording every visitor's story. Your journey is now part of its "
                "eternal pages."
            ),
            is_start_node=False,
            is_end_node=True,
            created_at=now,
            updated_at=now,
        )
        session.add_all([node_1, node_2, node_3, node_4, node_5])

        # 3. Create Node Choices
        # From Node 1
        choice_1a = NodeChoice(
            from_node_id=DEMO_NODE_1_ID,
            to_node_id=DEMO_NODE_2_ID,
            text="Enter the Reading Room",
            order=0,
        )
        choice_1b = NodeChoice(
            from_node_id=DEMO_NODE_1_ID,
            to_node_id=DEMO_NODE_3_ID,
            text="Go directly to the Restricted Section",
            order=1,
        )
        # From Node 2
        choice_2a = NodeChoice(
            from_node_id=DEMO_NODE_2_ID,
            to_node_id=DEMO_NODE_3_ID,
            text="Take the brass key and proceed",
            order=0,
            sets_state={"has_key": True},
        )
        choice_2b = NodeChoice(
            from_node_id=DEMO_NODE_2_ID,
            to_node_id=DEMO_NODE_3_ID,
            text="Leave the key and proceed",
            order=1,
        )
        # From Node 3
        choice_3a = NodeChoice(
            from_node_id=DEMO_NODE_3_ID,
            to_node_id=DEMO_NODE_4_ID,
            text="Try the hidden door",
            order=0,
            requires_state={"has_key": True},
        )
        choice_3b = NodeChoice(
            from_node_id=DEMO_NODE_3_ID,
            to_node_id=DEMO_NODE_5_ID,
            text="Speak with the librarian",
            order=1,
        )
        # From Node 4
        choice_4a = NodeChoice(
            from_node_id=DEMO_NODE_4_ID,
            to_node_id=DEMO_NODE_5_ID,
            text="Touch an orb",
            order=0,
        )
        session.add_all([choice_1a, choice_1b, choice_2a, choice_2b, choice_3a, choice_3b, choice_4a])

        # 4. Create Story State Variables
        state_var = StoryStateVariable(
            id=DEMO_STATE_VAR_ID,
            story_id=DEMO_STORY_ID,
            story_version=1,
            key="has_key",
            value_type=StateValueType.BOOLEAN,
            default_value=False,
            description="Whether the player has picked up the brass key",
            created_at=now,
            updated_at=now,
        )
        session.add(state_var)

        # 5. Create Room
        room = Room(
            room_id=DEMO_ROOM_ID,
            title="Story Runtime Demo Room",
            story_id=DEMO_STORY_ID,
            creator_id=owner_id,
            created_at=now,
            last_activity=now,
        )
        session.add(room)

        # 6. Create AgentConfig entries
        narrator = AgentConfig(
            id=DEMO_NARRATOR_ID,
            slug="demo-narrator",
            name="Narrator",
            description="Atmospheric storytelling agent for interactive fiction",
            model_name="openai:gpt-4o-mini",
            system_prompt=(
                "You are the Narrator, an atmospheric storytelling agent in an interactive "
                "fiction experience. You react to the player's current position in the story, "
                "describe the atmosphere, and hint at consequences of their choices. Keep "
                "responses to 2-3 sentences. Reference the current node content and available "
                "choices naturally. If the player is at an end node, provide a satisfying "
                "conclusion."
            ),
            participation_mode="always",
            scope="system",
            is_enabled=True,
            owner_id=owner_id,
            created_at=now,
        )
        guide = AgentConfig(
            id=DEMO_GUIDE_ID,
            slug="demo-guide",
            name="Guide",
            description="Helpful companion agent for interactive fiction",
            model_name="openai:gpt-4o-mini",
            system_prompt=(
                "You are the Guide, a helpful companion in an interactive fiction experience. "
                "You reference the player's story state (items collected, choices made) and "
                "suggest which choices might align with their journey so far. Keep responses "
                "to 2-3 sentences. If the player has the brass key, hint that it might be "
                "useful. Track the path they've taken via the node chain."
            ),
            participation_mode="always",
            scope="system",
            is_enabled=True,
            owner_id=owner_id,
            created_at=now,
        )
        session.add_all([narrator, guide])

        # 7. Create RoomParticipants for both agents
        participant_narrator = RoomParticipant(
            room_id=DEMO_ROOM_ID,
            participant_id="demo-narrator",
            participant_type="agent",
            role="agent",
            active=True,
            joined_at=now,
        )
        participant_guide = RoomParticipant(
            room_id=DEMO_ROOM_ID,
            participant_id="demo-guide",
            participant_type="agent",
            role="agent",
            active=True,
            joined_at=now,
        )
        session.add_all([participant_narrator, participant_guide])

        # 8. Create Persona + UserPersona
        persona = Persona(
            id=DEMO_PERSONA_ID,
            name="Demo Explorer",
            description="A curious explorer of enchanted places",
            created_at=now,
        )
        session.add(persona)

        user_persona = UserPersona(
            id=DEMO_USER_PERSONA_ID,
            user_id=owner_id,
            persona_id=DEMO_PERSONA_ID,
            created_at=now,
        )
        session.add(user_persona)

        # 9. Create UserStoryProgress (runtime initialization)
        progress = UserStoryProgress(
            id=DEMO_PROGRESS_ID,
            user_persona_id=DEMO_USER_PERSONA_ID,
            story_id=DEMO_STORY_ID,
            story_version=1,
            current_node_id=DEMO_NODE_1_ID,
            story_state={"has_key": False},
            is_completed=False,
            head_version=0,
            started_at=now,
            updated_at=now,
        )
        session.add(progress)

        # Create RoomStoryProgress pointing to the UserStoryProgress
        room_progress = RoomStoryProgress(
            id=DEMO_ROOM_PROGRESS_ID,
            room_id=DEMO_ROOM_ID,
            story_id=DEMO_STORY_ID,
            story_version=1,
            active_progress_id=DEMO_PROGRESS_ID,
            revision=0,
            created_at=now,
            updated_at=now,
        )
        session.add(room_progress)

        # Commit all entities
        await session.commit()

        print("Demo story runtime seeded successfully!")
        print(f"Room UUID: {DEMO_ROOM_ID}")
        print(f"Story UUID: {DEMO_STORY_ID}")
        print(f"Story: 'The Enchanted Library' (5 nodes, published)")
        print(f"Agents: demo-narrator, demo-guide")
        print(f"Persona: Demo Explorer")


if __name__ == "__main__":
    asyncio.run(seed())
