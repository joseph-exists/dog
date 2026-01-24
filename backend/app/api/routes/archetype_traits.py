import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Archetype,
    ArchetypeTraitLink,
    Message,
    Trait,
    TraitPublic,
)

router = APIRouter(
    prefix="/archetypes/{archetype_id}/traits", tags=["archetype-traits"]
)


@router.get("/", response_model=list[TraitPublic])
def read_archetype_traits(
    session: SessionDep, current_user: CurrentUser, archetype_id: uuid.UUID
) -> Any:
    """
    Get all traits for an archetype.
    """
    archetype = session.get(Archetype, archetype_id)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")

    statement = (
        select(Trait)
        .join(ArchetypeTraitLink, ArchetypeTraitLink.trait_id == Trait.id)
        .where(ArchetypeTraitLink.archetype_id == archetype_id)
    )
    traits = session.exec(statement).all()
    return traits


@router.post("/{trait_id}", response_model=Message)
def add_trait_to_archetype(
    session: SessionDep,
    current_user: CurrentUser,
    archetype_id: uuid.UUID,
    trait_id: uuid.UUID,
) -> Any:
    """
    Add a trait to an archetype.
    """
    archetype = session.get(Archetype, archetype_id)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")

    trait = session.get(Trait, trait_id)
    if not trait:
        raise HTTPException(status_code=404, detail="Trait not found")

    # Check if link already exists
    existing = session.exec(
        select(ArchetypeTraitLink).where(
            ArchetypeTraitLink.archetype_id == archetype_id,
            ArchetypeTraitLink.trait_id == trait_id,
        )
    ).first()
    if existing:
        return Message(message="Trait already linked to archetype")

    link = ArchetypeTraitLink(archetype_id=archetype_id, trait_id=trait_id)
    session.add(link)
    session.commit()
    return Message(message="Trait added to archetype successfully")


@router.delete("/{trait_id}", response_model=Message)
def remove_trait_from_archetype(
    session: SessionDep,
    current_user: CurrentUser,
    archetype_id: uuid.UUID,
    trait_id: uuid.UUID,
) -> Any:
    """
    Remove a trait from an archetype.
    """
    archetype = session.get(Archetype, archetype_id)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")

    link = session.exec(
        select(ArchetypeTraitLink).where(
            ArchetypeTraitLink.archetype_id == archetype_id,
            ArchetypeTraitLink.trait_id == trait_id,
        )
    ).first()
    if not link:
        raise HTTPException(
            status_code=404, detail="Trait not linked to archetype"
        )

    session.delete(link)
    session.commit()
    return Message(message="Trait removed from archetype successfully")
