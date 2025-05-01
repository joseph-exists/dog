""" testing traits """
import pytest
from pydantic import ValidationError
from sqlmodel import Session

from app.models import Trait, TraitCreate, TraitUpdate
from app.tests.utils.trait import create_random_trait


def test_trait_create_valid():
    """Test that TraitCreate validates correct data."""
    data = {
        "name": "Test Trait",
        "description": "A test trait description",
        # "archetype_only": True,
        # "max_active_personas": 5,
    }
    trait_create = TraitCreate(**data)
    assert trait_create.name == data["name"]
    assert trait_create.description == data["description"]
    # assert trait_create.archetype_only == data["archetype_only"]
    # assert trait_create.max_active_personas == data["max_active_personas"]

    # Test with minimal data (name only)
    minimal_data = {"name": "Minimal Trait"}
    minimal_trait = TraitCreate(**minimal_data)
    assert minimal_trait.name == minimal_data["name"]
    assert minimal_trait.description is None
    # assert minimal_trait.archetype_only is False
    #  assert minimal_trait.max_active_personas is None


def test_trait_create_invalid():
    """Test that TraitCreate rejects invalid data."""
    # Test with empty name
    with pytest.raises(ValidationError):
        TraitCreate(name="", description="Test description")

    # Test with name that's too long (more than 255 chars)
    with pytest.raises(ValidationError):
        TraitCreate(name="a" * 256, description="Test description")

    # Test with negative max_active_personas
    #  with pytest.raises(ValidationError):
    #   TraitCreate(name="Test Trait", max_active_personas=-1)


def test_trait_update_valid():
    """Test that TraitUpdate validates correct data."""
    # Test with all fields
    data = {
        "name": "Updated Trait",
        "description": "An updated trait description",
        # "archetype_only": False,
        # "max_active_personas": 10,
    }
    trait_update = TraitUpdate(**data)
    assert trait_update.name == data["name"]
    assert trait_update.description == data["description"]
    # assert trait_update.archetype_only == data["archetype_only"]
    # assert trait_update.max_active_personas == data["max_active_personas"]

    # Test with partial fields (only updating description and archetype_only)
    partial_data = {
        "description": "Only updating the description",
        # "archetype_only": True,
    }
    partial_update = TraitUpdate(**partial_data)
    assert partial_update.name is None
    assert partial_update.description == partial_data["description"]
    # assert partial_update.archetype_only == partial_data["archetype_only"]
    # assert partial_update.max_active_personas is None


def test_trait_db_operations(db: Session):
    """Test database operations with the Trait model."""
    # Create a trait
    trait = create_random_trait(db)
    assert trait.id is not None
    assert trait.name is not None
    assert trait.created_at is not None
    # assert trait.updated_at is None
    # assert trait.archetype_only is True
    # assert trait.max_active_personas == 3

    # Create another trait with different settings
    trait2 = create_random_trait(db)
    assert trait2.id is not None
    # assert trait2.archetype_only is False
    # assert trait2.max_active_personas is None

    # Update the first trait
    original_name = trait.name
    new_name = "Updated Name"
    trait.name = new_name
    # trait.archetype_only = False
    db.add(trait)
    db.commit()
    db.refresh(trait)

    # Verify update
    assert trait.name == new_name
    assert trait.name != original_name
    # assert trait.archetype_only is False

    # Delete the traits
    db.delete(trait)
    db.delete(trait2)
    db.commit()

    # Verify deletion
    fetched_trait = db.get(Trait, trait.id)
    assert fetched_trait is None
    fetched_trait2 = db.get(Trait, trait2.id)
    assert fetched_trait2 is None
