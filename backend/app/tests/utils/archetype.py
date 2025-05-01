from sqlmodel import Session

from app import crud
from app.models import Archetype, ArchetypeCreate
from app.tests.utils.utils import random_lower_string


def create_random_archetype(db: Session) -> Archetype:
    name = random_lower_string()
    description = random_lower_string()
    # Generate a valid archetype_name from title
    archetype_name = name[:20].lower().replace(" ", "_")

    archetype_in = ArchetypeCreate(name=name, description=description)

    # Create the archetype instance directly because the crud function has issues
    archetype = Archetype.model_validate(
        archetype_in,
        update={
            "enabled": True,
            "archetype_name": archetype_name
        }
    )
    db.add(archetype)
    db.commit()
    db.refresh(archetype)
    return archetype
