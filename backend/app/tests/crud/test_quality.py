import pytest
from pydantic import ValidationError
from sqlmodel import Session

from app.models import Quality, QualityCreate, QualityUpdate
from app.tests.utils.quality import create_random_quality


def test_quality_create_valid():
    """Test that QualityCreate validates correct data."""
    data = {
        "name": "Test Quality",
        "description": "A test quality description"
    }
    quality_create = QualityCreate(**data)
    assert quality_create.name == data["name"]
    assert quality_create.description == data["description"]


def test_quality_create_invalid():
    """Test that QualityCreate rejects invalid data."""
    # Test with empty name
    with pytest.raises(ValidationError):
        QualityCreate(name="", description="Test description")

    # Test with name that's too long (more than 255 chars)
    with pytest.raises(ValidationError):
        QualityCreate(name="a" * 256, description="Test description")


def test_quality_update_valid():
    """Test that QualityUpdate validates correct data."""
    # Test with all fields
    data = {
        "name": "Updated Quality",
        "description": "An updated quality description"
    }
    quality_update = QualityUpdate(**data)
    assert quality_update.name == data["name"]
    assert quality_update.description == data["description"]

    # Test with partial fields (only updating description)
    partial_data = {
        "description": "Only updating the description"
    }
    partial_update = QualityUpdate(**partial_data)
    assert partial_update.name is None
    assert partial_update.description == partial_data["description"]


def test_quality_db_operations(db: Session):
    """Test database operations with the Quality model."""
    # Create a quality
    quality = create_random_quality(db)
    assert quality.id is not None
    assert quality.created_at is not None
    assert quality.updated_at is None

    # Update the quality
    original_name = quality.name
    new_name = "Updated Name"
    quality.name = new_name
    db.add(quality)
    db.commit()
    db.refresh(quality)

    # Verify update
    assert quality.name == new_name
    assert quality.name != original_name

    # Delete the quality
    db.delete(quality)
    db.commit()
    
    # Verify deletion
    fetched_quality = db.get(Quality, quality.id)
    assert fetched_quality is None
