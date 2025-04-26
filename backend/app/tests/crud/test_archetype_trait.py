from sqlmodel import Session, select

from app.models import ArchetypeTraitLink, Archetype, Trait
from app.tests.utils.archetype import create_random_archetype
from app.tests.utils.trait import create_random_trait
from app.tests.utils.archetype_trait import create_archetype_trait_link


def test_create_archetype_trait_link(db: Session):
    """Test creating a relationship between an archetype and a trait."""
    archetype = create_random_archetype(db)
    trait = create_random_trait(db)

    link = ArchetypeTraitLink(
        archetype_id=archetype.id,
        trait_id=trait.id,
        is_modifiable=True,
        modifiable_at_creation_only=False,
        is_required=True,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    assert link.archetype_id == archetype.id
    assert link.trait_id == trait.id
    assert link.is_modifiable is True
    assert link.modifiable_at_creation_only is False
    assert link.is_required is True
    assert link.created_at is not None
    assert link.updated_at is None


def test_archetype_trait_relationship(db: Session):
    """Test the relationship between archetypes and traits."""
    # Create an archetype and two traits
    archetype = create_random_archetype(db)
    trait1 = create_random_trait(db)
    trait2 = create_random_trait(db)

    # Create links with different configurations
    link1 = create_archetype_trait_link(
        db,
        archetype_id=archetype.id,
        trait_id=trait1.id,
        is_modifiable=True,
        is_required=True,
    )

    link2 = create_archetype_trait_link(
        db,
        archetype_id=archetype.id,
        trait_id=trait2.id,
        is_modifiable=False,
        modifiable_at_creation_only=True,
        is_required=False,
    )

    # Verify trait_links relationship
    db.refresh(archetype)
    assert len(archetype.trait_links) == 2

    # Verify traits relationship
    assert len(archetype.traits) == 2
    trait_ids = [trait.id for trait in archetype.traits]
    assert trait1.id in trait_ids
    assert trait2.id in trait_ids

    # Verify archetype_links relationship in traits
    db.refresh(trait1)
    db.refresh(trait2)
    assert len(trait1.archetype_links) == 1
    assert len(trait2.archetype_links) == 1

    # Verify archetypes relationship in traits
    assert len(trait1.archetypes) == 1
    assert len(trait2.archetypes) == 1
    assert trait1.archetypes[0].id == archetype.id
    assert trait2.archetypes[0].id == archetype.id


def test_update_archetype_trait_link(db: Session):
    """Test updating a trait configuration in an archetype."""
    link = create_archetype_trait_link(db)

    # Update the link configuration
    link.is_modifiable = False
    link.modifiable_at_creation_only = True

    db.add(link)
    db.commit()
    db.refresh(link)

    assert link.is_modifiable is False
    assert link.modifiable_at_creation_only is True


def test_delete_archetype_trait_link(db: Session):
    """Test removing a trait from an archetype."""
    archetype = create_random_archetype(db)
    trait = create_random_trait(db)

    link = create_archetype_trait_link(db, archetype_id=archetype.id, trait_id=trait.id)

    # Delete the link
    db.delete(link)
    db.commit()

    # Verify deletion
    statement = select(ArchetypeTraitLink).where(
        (ArchetypeTraitLink.archetype_id == archetype.id)
        & (ArchetypeTraitLink.trait_id == trait.id)
    )
    result = db.exec(statement).first()
    assert result is None

    # Verify archetype and trait still exist
    db.refresh(archetype)
    db.refresh(trait)
    assert db.get(Archetype, archetype.id) is not None
    assert db.get(Trait, trait.id) is not None


def test_cascade_delete_archetype(db: Session):
    """Test that deleting an archetype also deletes all its trait links."""
    archetype = create_random_archetype(db)
    trait1 = create_random_trait(db)
    trait2 = create_random_trait(db)

    link1 = create_archetype_trait_link(
        db, archetype_id=archetype.id, trait_id=trait1.id
    )

    link2 = create_archetype_trait_link(
        db, archetype_id=archetype.id, trait_id=trait2.id
    )

    # Delete the archetype
    db.delete(archetype)
    db.commit()

    # Verify links are deleted
    statement = select(ArchetypeTraitLink).where(
        ArchetypeTraitLink.archetype_id == archetype.id
    )
    results = db.exec(statement).all()
    assert len(results) == 0

    # Verify traits still exist
    assert db.get(Trait, trait1.id) is not None
    assert db.get(Trait, trait2.id) is not None


def test_cascade_delete_trait(db: Session):
    """Test that deleting a trait also deletes all its archetype links."""
    archetype1 = create_random_archetype(db)
    archetype2 = create_random_archetype(db)
    trait = create_random_trait(db)

    link1 = create_archetype_trait_link(
        db, archetype_id=archetype1.id, trait_id=trait.id
    )

    link2 = create_archetype_trait_link(
        db, archetype_id=archetype2.id, trait_id=trait.id
    )

    # Delete the trait
    db.delete(trait)
    db.commit()

    # Verify links are deleted
    statement = select(ArchetypeTraitLink).where(
        ArchetypeTraitLink.trait_id == trait.id
    )
    results = db.exec(statement).all()
    assert len(results) == 0

    # Verify archetypes still exist
    assert db.get(Archetype, archetype1.id) is not None
    assert db.get(Archetype, archetype2.id) is not None
