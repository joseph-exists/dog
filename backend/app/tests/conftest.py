from collections.abc import AsyncGenerator, Generator
import logging
import os
import sys
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import Session, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

# Set dummy OpenAI API key for tests (before app imports)
# This prevents OpenAI client initialization errors during agent module loading
# Actual API calls in tests should be mocked
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-testing")

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import (
    Item,
    Room,
    RoomMessage,
    RoomParticipant,
    Story,
    User,
    UserCreate,
)
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def db() -> Generator[Session, None, None]:
    logger.info("Initializing test database")
    with Session(engine) as session:
        init_db(session)
        yield session
        logger.info("Cleaning up test database")
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    logger.info("Creating test client")
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    logger.info("Setting up superuser token headers")
    # Ensure superuser exists
    user = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()

    if not user:
        logger.info(f"Creating superuser with email: {settings.FIRST_SUPERUSER}")
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        from app import crud

        user = crud.create_user(session=db, user_create=user_in)
        logger.info(f"Superuser created with ID: {user.id}")
        db.commit()
    else:
        logger.info(f"Superuser already exists with ID: {user.id}")

    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    logger.info("Setting up normal user token headers")
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


# =============================================================================
# Sync Room Fixtures for Integration Tests (API tests)
# =============================================================================


@pytest.fixture(name="api_test_room")
def sync_test_room(db: Session) -> Room:
    """Create a test room owned by superuser for API integration tests."""
    from datetime import datetime, timezone

    # Get superuser
    superuser = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()

    room = Room(
        room_id=uuid4(),
        creator_id=superuser.id,
        title="Test Room",
        story_id=None,
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    db.add(room)

    # Add superuser as participant
    participant = RoomParticipant(
        room_id=room.room_id,
        participant_id=str(superuser.id),
        participant_type="user",
        role="owner",
        active=True,
    )
    db.add(participant)
    db.commit()
    db.refresh(room)
    return room


@pytest.fixture(name="api_test_room_with_agent")
def sync_test_room_with_agent(db: Session) -> Room:
    """Create a test room with StoryAdvisor agent for API integration tests."""
    from datetime import datetime, timezone

    # Get superuser
    superuser = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()

    room = Room(
        room_id=uuid4(),
        creator_id=superuser.id,
        title="Test Room with Agent",
        story_id=None,
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    db.add(room)

    # Add superuser as participant
    user_participant = RoomParticipant(
        room_id=room.room_id,
        participant_id=str(superuser.id),
        participant_type="user",
        role="owner",
        active=True,
    )
    db.add(user_participant)

    # Add StoryAdvisor agent as participant
    agent_participant = RoomParticipant(
        room_id=room.room_id,
        participant_id="StoryAdvisor",
        participant_type="agent",
        role="member",
        active=True,
    )
    db.add(agent_participant)

    db.commit()
    db.refresh(room)
    return room


# =============================================================================
# Async Session Fixtures for Agent Tests
# =============================================================================

# Create async engine for tests
async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI).replace(
        "postgresql+psycopg://", "postgresql+psycopg://"
    ),
    echo=False,
)


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[SQLModelAsyncSession, None]:
    """Provide async database session for tests."""
    async with SQLModelAsyncSession(
        async_engine, expire_on_commit=False
    ) as session:
        yield session
        await session.rollback()  # Rollback any uncommitted changes after test


# =============================================================================
# Room Test Fixtures
# =============================================================================


@pytest_asyncio.fixture(scope="function")
async def test_user(async_session: SQLModelAsyncSession) -> User:
    """Create a test user with unique email."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email=f"testuser-{user_id}@example.com",
        hashed_password="hashed",
        is_superuser=False,
        is_active=True,
        full_name="Test User",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_story(async_session: SQLModelAsyncSession, test_user: User) -> Story:
    """Create a test story."""
    story = Story(
        id=uuid4(),
        title="Test Story",
        description="A test story for agent tests",
        owner_id=test_user.id,
        is_published=False,
    )
    async_session.add(story)
    await async_session.commit()
    await async_session.refresh(story)
    return story


@pytest_asyncio.fixture(scope="function")
async def test_room(async_session: SQLModelAsyncSession, test_user: User) -> Room:
    """Create a basic test room without story."""
    from datetime import datetime, timezone

    room = Room(
        room_id=uuid4(),
        creator_id=test_user.id,
        title="Test Room",
        story_id=None,
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    async_session.add(room)

    # Add creator as participant
    participant = RoomParticipant(
        room_id=room.room_id,
        participant_id=str(test_user.id),
        participant_type="user",
        role="owner",
        active=True,
    )
    async_session.add(participant)

    await async_session.commit()
    await async_session.refresh(room)
    return room


@pytest_asyncio.fixture(scope="function")
async def test_room_with_story(
    async_session: SQLModelAsyncSession, test_user: User, test_story: Story
) -> Room:
    """Create a test room with an associated story."""
    from datetime import datetime, timezone

    room = Room(
        room_id=uuid4(),
        creator_id=test_user.id,
        title="Test Room with Story",
        story_id=test_story.id,
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    async_session.add(room)

    # Add creator as participant
    participant = RoomParticipant(
        room_id=room.room_id,
        participant_id=str(test_user.id),
        participant_type="user",
        role="owner",
        active=True,
    )
    async_session.add(participant)

    await async_session.commit()
    await async_session.refresh(room)
    return room


@pytest_asyncio.fixture(scope="function")
async def test_room_with_messages(
    async_session: SQLModelAsyncSession, test_room: Room, test_user: User
) -> Room:
    """Create a test room with several messages."""
    from datetime import datetime, timezone, timedelta

    base_time = datetime.now(timezone.utc)

    for i in range(3):
        message = RoomMessage(
            message_id=uuid4(),
            room_id=test_room.room_id,
            sender_type="user",
            sender_id=test_user.id,
            agent_name=None,
            content=f"Test message {i + 1}",
            created_at=base_time + timedelta(seconds=i),
        )
        async_session.add(message)

    await async_session.commit()
    await async_session.refresh(test_room)
    return test_room


@pytest_asyncio.fixture(scope="function")
async def test_room_with_participants(
    async_session: SQLModelAsyncSession, test_room: Room
) -> Room:
    """Create a test room with multiple participants."""
    # Add another user participant
    participant = RoomParticipant(
        room_id=test_room.room_id,
        participant_id=str(uuid4()),
        participant_type="user",
        role="member",
        active=True,
    )
    async_session.add(participant)

    await async_session.commit()
    await async_session.refresh(test_room)
    return test_room


@pytest_asyncio.fixture(scope="function")
async def test_room_with_agent(
    async_session: SQLModelAsyncSession, test_room: Room
) -> Room:
    """Create a test room with StoryAdvisor agent as participant."""
    participant = RoomParticipant(
        room_id=test_room.room_id,
        participant_id="StoryAdvisor",
        participant_type="agent",
        role="member",
        active=True,
    )
    async_session.add(participant)

    await async_session.commit()
    await async_session.refresh(test_room)
    return test_room


@pytest_asyncio.fixture(scope="function")
async def test_room_with_multiple_agents(
    async_session: SQLModelAsyncSession, test_room: Room
) -> Room:
    """Create a test room with multiple agent participants."""
    agents = ["StoryAdvisor", "TestAgent2"]

    for agent_name in agents:
        participant = RoomParticipant(
            room_id=test_room.room_id,
            participant_id=agent_name,
            participant_type="agent",
            role="member",
            active=True,
        )
        async_session.add(participant)

    await async_session.commit()
    await async_session.refresh(test_room)
    return test_room
