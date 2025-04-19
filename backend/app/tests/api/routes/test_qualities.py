import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.tests.utils.quality import create_random_quality


def test_read_qualities(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # This test checks if the quality model is properly migrated
    # and accessible in the database
    quality = create_random_quality(db)
    assert quality.id is not None
    assert quality.name is not None
    assert quality.created_at is not None
