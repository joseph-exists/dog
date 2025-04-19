from sqlmodel import Session

from app.models import ArchetypeTraitLink, Archetype, Trait
from app.tests.utils.archetype import create_random_archetype
from app.tests.utils.trait import create_random_trait


def create_archetype_trait_link(
    db: Session,
    archetype_id=None,
    trait_id=None,
    is_modifiable=True,
    modifiable_at_creation_only=False,
    is_required=False
) -> ArchetypeTraitLink:
    """
    Create a relationship between an archetype and a trait for testing.
    If archetype_id or trait_id is not provided, a new entity is created.
    """
    if archetype_id is None:
        archetype = create_random_archetype(db)
        archetype_id = archetype.id
    
    if trait_id is None:
        trait = create_random_trait(db)
        trait_id = trait.id
    
    link = ArchetypeTraitLink(
        archetype_id=archetype_id,
        trait_id=trait_id,
        is_modifiable=is_modifiable,
        modifiable_at_creation_only=modifiable_at_creation_only,
        is_required=is_required
    )
    
    db.add(link)
    db.commit()
    db.refresh(link)
    return link
