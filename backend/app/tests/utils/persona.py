from sqlmodel import Session

from app import crud
from app.models import Persona, PersonaCreate
from app.tests.utils.user import create_random_user
from app.tests.utils.archetype import create_random_archetype
from app.tests.utils.utils import random_lower_string


def create_random_persona(db: Session, archetype_id=None) -> Persona:
    user = create_random_user(db)
    owner_id = user.id
    assert owner_id is not None

    # If no archetype_id is provided, create a random archetype
    if archetype_id is None:
        archetype = create_random_archetype(db)
        archetype_id = archetype.id

    name = random_lower_string()
    description = random_lower_string()
    # Generate a valid persona_name from name
    persona_name = name[:20].lower().replace(" ", "_")

    persona_in = PersonaCreate(name=name, description=description)

    # Create the persona instance directly because the crud function has issues
    persona = Persona.model_validate(
        persona_in,
        update={
            "persona_name": persona_name,
        },
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona
