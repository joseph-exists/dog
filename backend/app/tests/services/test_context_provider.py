"""Tests for Context Provider Service."""
import pytest
from uuid import uuid4

from app.services.context_provider import build_room_context, RoomContext


class TestContextProvider:
    """Test suite for context provider."""

    @pytest.mark.asyncio
    async def test_build_context_for_room_without_story(
        self, async_session, test_room
    ):
        """Context should work for rooms without associated stories."""
        context = await build_room_context(
            room_id=test_room.room_id,
            session=async_session,
        )

        assert isinstance(context, RoomContext)
        assert context.room_id == test_room.room_id
        assert context.story_data is None
        assert context.room_metadata["title"] == test_room.title

    @pytest.mark.asyncio
    async def test_build_context_with_story(
        self, async_session, test_room_with_story
    ):
        """Context should include story data when available."""
        context = await build_room_context(
            room_id=test_room_with_story.room_id,
            session=async_session,
        )

        assert context.story_data is not None
        assert "title" in context.story_data
        assert "description" in context.story_data

    @pytest.mark.asyncio
    async def test_build_context_includes_recent_messages(
        self, async_session, test_room_with_messages
    ):
        """Context should include recent messages."""
        context = await build_room_context(
            room_id=test_room_with_messages.room_id,
            session=async_session,
            message_limit=5,
        )

        assert len(context.recent_messages) <= 5
        # Messages should be in chronological order
        if len(context.recent_messages) > 1:
            first_time = context.recent_messages[0]["created_at"]
            last_time = context.recent_messages[-1]["created_at"]
            assert first_time <= last_time

    @pytest.mark.asyncio
    async def test_build_context_includes_participants(
        self, async_session, test_room_with_participants
    ):
        """Context should list active participants."""
        context = await build_room_context(
            room_id=test_room_with_participants.room_id,
            session=async_session,
        )

        assert len(context.participants) > 0
        # All participants should be active
        for p in context.participants:
            assert "participant_type" in p
            assert "role" in p

    @pytest.mark.asyncio
    async def test_build_context_nonexistent_room_raises(
        self, async_session
    ):
        """Should raise ValueError for non-existent room."""
        with pytest.raises(ValueError, match="not found"):
            await build_room_context(
                room_id=uuid4(),
                session=async_session,
            )
