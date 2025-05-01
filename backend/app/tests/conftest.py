from collections.abc import Generator
import logging
import sys

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, User, UserCreate
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
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
