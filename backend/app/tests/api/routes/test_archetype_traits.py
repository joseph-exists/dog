import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import ArchetypeTraitLink, Archetype, Trait
from app.tests.utils.archetype import create_random_archetype
from app.tests.utils.trait import create_random_trait
from app.tests.utils.archetype_trait import create_archetype_trait_link


def test_archetype_trait_link_db_structure(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """
    Test that the ArchetypeTraitLink model is properly migrated and functional.
    This is a basic database structure test, not an API test since the endpoints
    aren't implemented yet.
    """
    # Create test data
    archetype = create_random_archetype(db)
    trait = create_random_trait(db)

    # Create the link
    link = create_archetype_trait_link(
        db,
        archetype_id=archetype.id,
        trait_id=trait.id,
        is_modifiable=True,
        modifiable_at_creation_only=False,
        is_required=True,
    )

    # Verify the link exists and has the correct properties
    statement = select(ArchetypeTraitLink).where(
        (ArchetypeTraitLink.archetype_id == archetype.id)
        & (ArchetypeTraitLink.trait_id == trait.id)
    )
    result = db.exec(statement).one()

    assert result is not None
    assert result.archetype_id == archetype.id
    assert result.trait_id == trait.id
    assert result.is_modifiable is True
    assert result.modifiable_at_creation_only is False
    assert result.is_required is True

    # Test relationships
    db.refresh(archetype)
    db.refresh(trait)

    assert len(archetype.trait_links) > 0
    assert archetype.trait_links[0].trait_id == trait.id

    assert len(trait.archetype_links) > 0
    assert trait.archetype_links[0].archetype_id == archetype.id
