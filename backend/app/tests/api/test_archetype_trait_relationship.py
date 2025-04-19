"""""
import uuid
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.models import Archetype, Trait, ArchetypeTraitLink


def test_archetype_trait_link_relationship():
  # note: uncomment the following line and convert back to docstring as needed
  #  Test the relationship between Archetype, Trait and ArchetypeTraitLink.
    # Create an in-memory database for testing
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    # Create a session
    with Session(engine) as session:
        # Create an archetype
        archetype = Archetype(
            id=uuid.uuid4(),  # Generate a UUID for the test
            title="Test Archetype",
            description="Test description",
            archetype_name="test_archetype",
            enabled=True
        )
        session.add(archetype)

        # Create a trait
        trait = Trait(
            id=uuid.uuid4(),  # Generate a UUID for the test
            name="Test Trait",
            description="Test trait description",
            archetype_only=False,
            max_active_personas=None
        )
        session.add(trait)

        # Commit to get IDs assigned
        session.commit()
        session.refresh(archetype)
        session.refresh(trait)

        # Create the link with configuration
        link = ArchetypeTraitLink(
            archetype_id=archetype.id,
            trait_id=trait.id,
            is_modifiable=True,
            modifiable_at_creation_only=False,
            is_required=True
        )
        session.add(link)
        session.commit()

        # Refresh all objects to load relationships
        session.refresh(archetype)
        session.refresh(trait)
        session.refresh(link)

        # Test relationships
        # 1. Direct link -> parent relationships
        assert link.archetype.id == archetype.id
        assert link.trait.id == trait.id

        # 2. Parent -> link relationships
        assert len(archetype.trait_links) == 1
        assert archetype.trait_links[0].trait_id == trait.id
        assert len(trait.archetype_links) == 1
        assert trait.archetype_links[0].archetype_id == archetype.id

        # 3. Many-to-many convenience relationships
        assert len(archetype.traits) == 1
        assert archetype.traits[0].id == trait.id
        assert len(trait.archetypes) == 1
        assert trait.archetypes[0].id == archetype.id

        # 4. Test configuration stored in link
        assert archetype.trait_links[0].is_required == True
        assert trait.archetype_links[0].is_modifiable == True
"""""
