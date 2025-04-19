import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.tests.utils.trait import create_random_trait


def test_read_traits(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # This test checks if the trait model is properly migrated
    # and accessible in the database
    trait = create_random_trait(db, archetype_only=True, max_active_personas=5)
    assert trait.id is not None
    assert trait.name is not None
    assert trait.created_at is not None
    assert trait.archetype_only is True
    assert trait.max_active_personas == 5
