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
    NodeChoice,
    Persona,
    Room,
    RoomMessage,
    RoomParticipant,
    Story,
    StoryNode,
    User,
    UserCreate,
    UserPersona,
    UserStoryProgress,
    ProgressSnapshot,
    ProgressSnapshotsPublic,
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
    user = db.exec(select(User).where(User.email == settings.FIRST_SUPERTESTUSER)).first()

    if not user:
        logger.info(f"Creating superuser with email: {settings.FIRST_SUPERTESTUSER}")
        user_in = UserCreate(
            email=settings.FIRST_SUPERTESTUSER,
            password=settings.FIRST_SUPERTESTUSER_PASSWORD,
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
        select(User).where(User.email == settings.FIRST_SUPERTESTUSER)
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
        select(User).where(User.email == settings.FIRST_SUPERTESTUSER)
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


# =============================================================================
# Story Progress Fixtures for Phase 1/2/3 Tests
# =============================================================================


@pytest.fixture(scope="function")
def db_story_with_progress(db: Session) -> tuple[Story, UserStoryProgress]:
    """
    Create a complete test story with progress for testing timeline features.

    Returns tuple of (Story, UserStoryProgress) with:
    - A test user
    - A test persona
    - A user persona instance
    - A story with multiple nodes and choices
    - A user story progress instance at the start
    """
    # Get or create test user (reuse superuser for simplicity)
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    if not user:
        from app import crud
        user_in = UserCreate(
            email=settings.EMAIL_TEST_USER,
            password="password",
            is_superuser=False,
        )
        user = crud.create_user(session=db, user_create=user_in)
        db.commit()
        db.refresh(user)

    # Create a test Persona
    persona = Persona(
        id=uuid4(),
        name="Test Persona",
        description="A test persona for story testing",
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)

    # Create UserPersona linking user to persona
    user_persona = UserPersona(
        id=uuid4(),
        user_id=user.id,
        persona_id=persona.id,
        nickname="Test Character",
        is_active=True,
    )
    db.add(user_persona)
    db.commit()
    db.refresh(user_persona)

    # Create a Story
    story = Story(
        id=uuid4(),
        title="Test Story for Timeline",
        description="A test story with nodes and choices",
        owner_id=user.id,
        is_published=True,
        current_version=1,
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    # Create story nodes
    start_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Start Node",
        content="You begin your adventure...",
        node_type="text",
        is_start_node=True,
        is_end_node=False,
    )
    db.add(start_node)

    node2 = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Second Node",
        content="You continue your journey...",
        node_type="text",
        is_start_node=False,
        is_end_node=False,
    )
    db.add(node2)

    node3 = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Third Node",
        content="You reach a crossroads...",
        node_type="text",
        is_start_node=False,
        is_end_node=False,
    )
    db.add(node3)

    node4 = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Fourth Node",
        content="You approach the finale...",
        node_type="text",
        is_start_node=False,
        is_end_node=False,
    )
    db.add(node4)

    node5 = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Fifth Node",
        content="The adventure concludes...",
        node_type="text",
        is_start_node=False,
        is_end_node=True,
    )
    db.add(node5)

    db.commit()
    db.refresh(start_node)
    db.refresh(node2)
    db.refresh(node3)
    db.refresh(node4)
    db.refresh(node5)

    # Create choices between nodes (4 choices for timeline tests)
    choice1 = NodeChoice(
        id=uuid4(),
        from_node_id=start_node.id,
        to_node_id=node2.id,
        text="Go forward",
        order=0,
    )
    db.add(choice1)

    choice2 = NodeChoice(
        id=uuid4(),
        from_node_id=node2.id,
        to_node_id=node3.id,
        text="Continue journey",
        order=0,
    )
    db.add(choice2)

    choice3 = NodeChoice(
        id=uuid4(),
        from_node_id=node3.id,
        to_node_id=node4.id,
        text="Press onward",
        order=0,
    )
    db.add(choice3)

    choice4 = NodeChoice(
        id=uuid4(),
        from_node_id=node4.id,
        to_node_id=node5.id,
        text="Finish the story",
        order=0,
    )
    db.add(choice4)

    db.commit()

    # Create UserStoryProgress at the start
    progress = UserStoryProgress(
        id=uuid4(),
        user_persona_id=user_persona.id,
        story_id=story.id,
        story_version=1,
        current_node_id=start_node.id,
        is_completed=False,
        story_state={},
        head_choice_id=None,  # At start, no choices made yet
        head_version=0,  # Version 0 = start
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)

    return (story, progress)

@pytest.fixture(scope="function")
def db_story_with_long_path(db: Session) -> tuple[Story, UserStoryProgress]:
    """
    Create a story with 60 nodes (59 choices) for testing snapshots.

    This fixture supports event sourcing tests that need to make 25-50 choices
    to test snapshot creation at 10-choice intervals.

    Structure: Linear path Start → N1 → N2 → ... → N59 → End

    Returns:
        tuple[Story, UserStoryProgress]: Story and progress at start (head_version=0)
    """
    # Get or create test user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    if not user:
        from app import crud
        user_in = UserCreate(
            email=settings.EMAIL_TEST_USER,
            password="password",
            is_superuser=False,
        )
        user = crud.create_user(session=db, user_create=user_in)
        db.commit()
        db.refresh(user)

    # Create Persona and UserPersona
    persona = Persona(
        id=uuid4(),
        name="Long Path Test Persona",
        description="For testing long story paths",
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)

    user_persona = UserPersona(
        id=uuid4(),
        user_id=user.id,
        persona_id=persona.id,
        nickname="Long Path Character",
        is_active=True,
    )
    db.add(user_persona)
    db.commit()
    db.refresh(user_persona)

    # Create Story
    story = Story(
        id=uuid4(),
        title="Long Path Test Story",
        description="A story with 60 nodes for testing snapshots",
        owner_id=user.id,
        is_published=True,
        current_version=1,
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    # Create 60 nodes (Start + 58 middle nodes + 1 end node)
    nodes = []

    # Start node
    start_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Start",
        content="Begin the long journey...",
        node_type="text",
        is_start_node=True,
        is_end_node=False,
    )
    db.add(start_node)
    nodes.append(start_node)

    # Create 58 middle nodes
    for i in range(1, 59):
        node = StoryNode(
            id=uuid4(),
            story_id=story.id,
            story_version=1,
            title=f"Node {i}",
            content=f"You continue to step {i}...",
            node_type="text",
            is_start_node=False,
            is_end_node=False,
        )
        db.add(node)
        nodes.append(node)

    # End node
    end_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="End",
        content="You have reached the end of the long path.",
        node_type="text",
        is_start_node=False,
        is_end_node=True,
    )
    db.add(end_node)
    nodes.append(end_node)

    db.commit()
    for node in nodes:
        db.refresh(node)

    # Create 59 choices connecting nodes sequentially
    for i in range(59):
        choice = NodeChoice(
            id=uuid4(),
            from_node_id=nodes[i].id,
            to_node_id=nodes[i + 1].id,
            text=f"Continue to step {i + 1}",
            order=0,
            sets_state={"step": i + 1},  # Track which step we're on
        )
        db.add(choice)

    db.commit()

    # Create UserStoryProgress at start
    progress = UserStoryProgress(
        id=uuid4(),
        user_persona_id=user_persona.id,
        story_id=story.id,
        story_version=1,
        current_node_id=start_node.id,
        is_completed=False,
        story_state={},
        head_choice_id=None,
        head_version=0,
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)

    return (story, progress)

@pytest.fixture(scope="function")
def db_story_with_simple_branch(db: Session) -> tuple[Story, UserStoryProgress]:
    """
    Create a story with simple branching: one branch point, two paths.

    Structure:
        Start Node (2 choices)
        ├─ "Go Left" → Left Node → "Continue Left" → Left End
        └─ "Go Right" → Right Node → "Continue Right" → Right End

    Use cases:
    - Test that node has multiple available_choices
    - Test that different choices lead to different nodes
    - Test that each branch has different subsequent choices
    - Test that state changes differ by branch

    Returns:
        tuple[Story, UserStoryProgress]: Story and progress at start
    """
    # Get or create test user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    if not user:
        from app import crud
        user_in = UserCreate(
            email=settings.EMAIL_TEST_USER,
            password="password",
            is_superuser=False,
        )
        user = crud.create_user(session=db, user_create=user_in)
        db.commit()
        db.refresh(user)

    # Create Persona and UserPersona
    persona = Persona(
        id=uuid4(),
        name="Branch Test Persona",
        description="For testing story branching",
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)

    user_persona = UserPersona(
        id=uuid4(),
        user_id=user.id,
        persona_id=persona.id,
        nickname="Branch Test Character",
        is_active=True,
    )
    db.add(user_persona)
    db.commit()
    db.refresh(user_persona)

    # Create Story
    story = Story(
        id=uuid4(),
        title="Simple Branch Test Story",
        description="A story with one branch point",
        owner_id=user.id,
        is_published=True,
        current_version=1,
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    # Create nodes
    start_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Crossroads",
        content="You stand at a crossroads. Which path do you take?",
        node_type="text",
        is_start_node=True,
        is_end_node=False,
    )
    db.add(start_node)

    left_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Left Path",
        content="You walk down the left path through the forest.",
        node_type="text",
        is_start_node=False,
        is_end_node=False,
    )
    db.add(left_node)

    right_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Right Path",
        content="You walk down the right path across the bridge.",
        node_type="text",
        is_start_node=False,
        is_end_node=False,
    )
    db.add(right_node)

    left_end = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Forest End",
        content="You emerge from the forest at a cottage.",
        node_type="text",
        is_start_node=False,
        is_end_node=True,
    )
    db.add(left_end)

    right_end = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Bridge End",
        content="You cross the bridge and reach a castle.",
        node_type="text",
        is_start_node=False,
        is_end_node=True,
    )
    db.add(right_end)

    db.commit()
    db.refresh(start_node)
    db.refresh(left_node)
    db.refresh(right_node)
    db.refresh(left_end)
    db.refresh(right_end)

    # Create choices - NOTE: Start has 2 choices
    choice_left = NodeChoice(
        id=uuid4(),
        from_node_id=start_node.id,
        to_node_id=left_node.id,
        text="Go left through the forest",
        order=0,
        sets_state={"path": "left", "environment": "forest"},
    )
    db.add(choice_left)

    choice_right = NodeChoice(
        id=uuid4(),
        from_node_id=start_node.id,
        to_node_id=right_node.id,
        text="Go right across the bridge",
        order=1,
        sets_state={"path": "right", "environment": "bridge"},
    )
    db.add(choice_right)

    choice_left_continue = NodeChoice(
        id=uuid4(),
        from_node_id=left_node.id,
        to_node_id=left_end.id,
        text="Continue through the forest",
        order=0,
        sets_state={"destination": "cottage"},
    )
    db.add(choice_left_continue)

    choice_right_continue = NodeChoice(
        id=uuid4(),
        from_node_id=right_node.id,
        to_node_id=right_end.id,
        text="Cross the bridge",
        order=0,
        sets_state={"destination": "castle"},
    )
    db.add(choice_right_continue)

    db.commit()

    # Create UserStoryProgress at start
    progress = UserStoryProgress(
        id=uuid4(),
        user_persona_id=user_persona.id,
        story_id=story.id,
        story_version=1,
        current_node_id=start_node.id,
        is_completed=False,
        story_state={},
        head_choice_id=None,
        head_version=0,
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)

    return (story, progress)
