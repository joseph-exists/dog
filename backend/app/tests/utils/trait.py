from sqlmodel import Session

from app.models import Trait
from app.tests.utils.utils import random_lower_string


def create_random_trait(db: Session) -> Trait:
    """
    Create a random trait entry for testing purposes.
    """
    name = random_lower_string()
    description = random_lower_string()

    trait = Trait(
        name=name,
        description=description,
        # archetype_only=archetype_only,
        # max_active_personas=max_active_personas
    )
    db.add(trait)
    db.commit()
    db.refresh(trait)
    return trait
