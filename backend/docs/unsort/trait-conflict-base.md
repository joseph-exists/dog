# Trait Conflict Models - Group-Based Approach

## Design Rationale

This implementation uses a **group-based** approach rather than pair-based for modeling trait conflicts. This supports:

- **Contradictory** (binary): Exactly 2 traits, mutually exclusive and exhaustive (Mortal/Immortal)
- **Contrary** (n-ary): 2+ traits where at most one can be true (Hot/Warm/Cold)
- **Subcontrary** (n-ary): 2+ traits where at least one must be true

This design aligns with Phase 3 of `backend/docs/carroll/CarrollSymbolicLogicImplementationPlan.md` and supports future extensibility for the inference engine (Phase 5), sorites chains, and complex paradoxes.

## References

- Phase 3 requirements: `backend/docs/carroll/CarrollSymbolicLogicImplementationPlan.md` (lines 541-561)
- Model patterns: `backend/docs/DATA_MODEL_RULES.md`
- Existing link table pattern: `ArchetypeTraitLink` in `backend/app/models.py`

---

## Model Definitions

```python
import uuid
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import Trait


# =============================================================================
# TRAIT CONFLICT GROUP - The conflict relationship container
# =============================================================================

class TraitConflictGroupBase(SQLModel):
    """Base model for TraitConflictGroup - shared properties."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    conflict_type: str = Field(
        max_length=50,
        description="Type of logical conflict: 'contradictory', 'contrary', or 'subcontrary'"
    )
    reason: str | None = Field(
        default=None,
        max_length=2000,
        description="Explanation of why these traits conflict - aids author judgment for edge cases"
    )


class TraitConflictGroupCreate(TraitConflictGroupBase):
    """Input model for creating a TraitConflictGroup."""
    # Optionally include initial trait IDs during creation
    trait_ids: list[uuid.UUID] | None = Field(
        default=None,
        description="Optional list of trait IDs to add as members during creation"
    )


class TraitConflictGroupUpdate(SQLModel):
    """Update model for TraitConflictGroup - all fields optional."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    conflict_type: str | None = Field(default=None, max_length=50)
    reason: str | None = Field(default=None, max_length=2000)


class TraitConflictGroup(TraitConflictGroupBase, table=True):
    """Database model for TraitConflictGroup."""
    __tablename__ = "traitconflictgroup"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)

    # Relationship to members (defined post-definition for circular ref safety)
    # members: list["TraitConflictGroupMember"] = Relationship(back_populates="group", cascade_delete=True)


class TraitConflictGroupPublic(TraitConflictGroupBase):
    """Public model for TraitConflictGroup API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None


class TraitConflictGroupPublicWithMembers(TraitConflictGroupPublic):
    """Public model with nested member traits for detailed responses."""
    members: list["TraitConflictGroupMemberPublic"] = []


class TraitConflictGroupsPublic(SQLModel):
    """Collection model for paginated TraitConflictGroup responses."""
    data: list[TraitConflictGroupPublic]
    count: int


# =============================================================================
# TRAIT CONFLICT GROUP MEMBER - Link table connecting traits to conflict groups
# =============================================================================

class TraitConflictGroupMemberBase(SQLModel):
    """Base model for TraitConflictGroupMember link."""
    # No additional base fields beyond the FKs


class TraitConflictGroupMemberCreate(SQLModel):
    """Input model for adding a trait to a conflict group."""
    trait_id: uuid.UUID = Field(description="ID of the trait to add to this conflict group")


class TraitConflictGroupMember(SQLModel, table=True):
    """Database model for TraitConflictGroupMember - links traits to conflict groups."""
    __tablename__ = "traitconflictgroupmember"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="traitconflictgroup.id", index=True)
    trait_id: uuid.UUID = Field(foreign_key="trait.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships (defined post-definition for circular ref safety)
    # group: "TraitConflictGroup" = Relationship(back_populates="members")
    # trait: "Trait" = Relationship(back_populates="conflict_memberships")


class TraitConflictGroupMemberPublic(SQLModel):
    """Public model for TraitConflictGroupMember API responses."""
    id: uuid.UUID
    group_id: uuid.UUID
    trait_id: uuid.UUID
    created_at: datetime


class TraitConflictGroupMembersPublic(SQLModel):
    """Collection model for paginated member responses."""
    data: list[TraitConflictGroupMemberPublic]
    count: int


# =============================================================================
# POST-DEFINITION RELATIONSHIP BINDINGS
# Add these at the end of models.py after all classes are defined
# =============================================================================

TraitConflictGroup.members = Relationship(
    back_populates="group",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)

TraitConflictGroupMember.group = Relationship(back_populates="members")
TraitConflictGroupMember.trait = Relationship(back_populates="conflict_memberships")

# Also add to Trait model:
Trait.conflict_memberships: list["TraitConflictGroupMember"] = Relationship(
    back_populates="trait"
)
```

---

## Usage Examples

### Example 1: Contradictory Traits (Binary - Mortal/Immortal)

```python
# Create the conflict group
group = TraitConflictGroup(
    name="Mortality Contradiction",
    conflict_type="contradictory",
    reason="A being cannot be both mortal (subject to death) and immortal (not subject to death). These are logical contradictories - one must be true, and exactly one.",
    description="Mortal and Immortal are mutually exclusive and exhaustive"
)

# Add members
TraitConflictGroupMember(group_id=group.id, trait_id=mortal_trait.id)
TraitConflictGroupMember(group_id=group.id, trait_id=immortal_trait.id)
```

### Example 2: Contrary Traits (N-ary - Temperature)

```python
# Create the conflict group
group = TraitConflictGroup(
    name="Temperature Contraries",
    conflict_type="contrary",
    reason="Temperature states are contraries: at most one can be true at a time, but none being true is valid (e.g., room temperature).",
    description="Hot, Warm, Cold cannot coexist"
)

# Add multiple members
TraitConflictGroupMember(group_id=group.id, trait_id=hot_trait.id)
TraitConflictGroupMember(group_id=group.id, trait_id=warm_trait.id)
TraitConflictGroupMember(group_id=group.id, trait_id=cold_trait.id)
```

### Example 3: Celarent Story (Reptiles/Mammals)

```python
# From test_carroll_celarent_story.py - E proposition: "No reptiles are mammals"
group = TraitConflictGroup(
    name="Thermoregulation Conflict",
    conflict_type="contradictory",
    reason="Cold-blooded (ectothermic) and warm-blooded (endothermic) are mutually exclusive metabolic strategies. This biological fact underlies the logical truth that reptiles and mammals form disjoint sets.",
    description="Cold-blooded and Warm-blooded traits cannot coexist"
)

TraitConflictGroupMember(group_id=group.id, trait_id=cold_blooded_trait.id)
TraitConflictGroupMember(group_id=group.id, trait_id=warm_blooded_trait.id)
```

---

## Validation Logic (for crud.py)

```python
def check_trait_conflicts(
    session: Session,
    persona_id: uuid.UUID,
    new_trait_id: uuid.UUID
) -> list[dict]:
    """
    Check if adding a trait would create a logical conflict.

    Returns list of conflicts found, empty if no conflicts.
    """
    # Get all conflict groups that include the new trait
    conflict_groups = session.exec(
        select(TraitConflictGroup)
        .join(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.trait_id == new_trait_id)
    ).all()

    # Get persona's current traits
    current_trait_ids = {
        link.trait_id for link in
        session.exec(
            select(PersonaTraitLink)
            .where(PersonaTraitLink.persona_id == persona_id)
        ).all()
    }

    conflicts = []
    for group in conflict_groups:
        # Get all trait IDs in this conflict group
        group_trait_ids = {
            member.trait_id for member in
            session.exec(
                select(TraitConflictGroupMember)
                .where(TraitConflictGroupMember.group_id == group.id)
            ).all()
        }

        # Check for overlap with current traits (excluding the new trait)
        conflicting_traits = current_trait_ids & group_trait_ids

        if conflicting_traits:
            conflicts.append({
                "group_id": group.id,
                "group_name": group.name,
                "conflict_type": group.conflict_type,
                "reason": group.reason,
                "conflicting_trait_ids": list(conflicting_traits)
            })

    return conflicts
```

---

## CRUD Functions (for crud.py)

```python
# =============================================================================
# TRAIT CONFLICT GROUP CRUD
# =============================================================================

def create_trait_conflict_group(
    *,
    session: Session,
    group_in: TraitConflictGroupCreate
) -> TraitConflictGroup:
    """
    Create a new trait conflict group, optionally with initial members.
    """
    # Validate conflict_type
    valid_types = {"contradictory", "contrary", "subcontrary"}
    if group_in.conflict_type not in valid_types:
        raise ValueError(f"conflict_type must be one of: {valid_types}")

    # Create the group (exclude trait_ids from model creation)
    group_data = group_in.model_dump(exclude={"trait_ids"})
    group = TraitConflictGroup.model_validate(group_data)
    session.add(group)
    session.commit()
    session.refresh(group)

    # Add initial members if provided
    if group_in.trait_ids:
        for trait_id in group_in.trait_ids:
            add_trait_to_conflict_group(
                session=session,
                group_id=group.id,
                member_in=TraitConflictGroupMemberCreate(trait_id=trait_id)
            )

    return group


def get_trait_conflict_group(
    *,
    session: Session,
    group_id: uuid.UUID
) -> TraitConflictGroup | None:
    """Get a trait conflict group by ID."""
    return session.get(TraitConflictGroup, group_id)


def get_trait_conflict_groups(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    conflict_type: str | None = None
) -> tuple[list[TraitConflictGroup], int]:
    """
    Get all trait conflict groups with optional filtering.
    Returns (groups, total_count).
    """
    query = select(TraitConflictGroup)

    if conflict_type:
        query = query.where(TraitConflictGroup.conflict_type == conflict_type)

    # Get count
    count_query = select(func.count()).select_from(query.subquery())
    count = session.exec(count_query).one()

    # Get paginated results
    groups = session.exec(query.offset(skip).limit(limit)).all()

    return list(groups), count


def update_trait_conflict_group(
    *,
    session: Session,
    db_group: TraitConflictGroup,
    group_in: TraitConflictGroupUpdate
) -> TraitConflictGroup:
    """Update an existing trait conflict group."""
    update_data = group_in.model_dump(exclude_unset=True)

    # Validate conflict_type if being updated
    if "conflict_type" in update_data:
        valid_types = {"contradictory", "contrary", "subcontrary"}
        if update_data["conflict_type"] not in valid_types:
            raise ValueError(f"conflict_type must be one of: {valid_types}")

    db_group.sqlmodel_update(update_data)
    db_group.updated_at = datetime.utcnow()
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group


def delete_trait_conflict_group(
    *,
    session: Session,
    group_id: uuid.UUID
) -> bool:
    """
    Delete a trait conflict group and all its members.
    Returns True if deleted, False if not found.
    """
    group = session.get(TraitConflictGroup, group_id)
    if not group:
        return False

    # Delete all members first (if cascade not configured)
    session.exec(
        delete(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.group_id == group_id)
    )

    session.delete(group)
    session.commit()
    return True


# =============================================================================
# TRAIT CONFLICT GROUP MEMBER CRUD
# =============================================================================

def add_trait_to_conflict_group(
    *,
    session: Session,
    group_id: uuid.UUID,
    member_in: TraitConflictGroupMemberCreate
) -> TraitConflictGroupMember:
    """
    Add a trait to a conflict group.
    Validates that the trait exists and isn't already in the group.
    """
    # Verify group exists
    group = session.get(TraitConflictGroup, group_id)
    if not group:
        raise ValueError(f"Conflict group {group_id} not found")

    # Verify trait exists
    trait = session.get(Trait, member_in.trait_id)
    if not trait:
        raise ValueError(f"Trait {member_in.trait_id} not found")

    # Check if already a member
    existing = session.exec(
        select(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.group_id == group_id)
        .where(TraitConflictGroupMember.trait_id == member_in.trait_id)
    ).first()

    if existing:
        raise ValueError(f"Trait {member_in.trait_id} is already in this conflict group")

    # Create the membership
    member = TraitConflictGroupMember(
        group_id=group_id,
        trait_id=member_in.trait_id
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def remove_trait_from_conflict_group(
    *,
    session: Session,
    group_id: uuid.UUID,
    trait_id: uuid.UUID
) -> bool:
    """
    Remove a trait from a conflict group.
    Returns True if removed, False if not found.
    """
    member = session.exec(
        select(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.group_id == group_id)
        .where(TraitConflictGroupMember.trait_id == trait_id)
    ).first()

    if not member:
        return False

    session.delete(member)
    session.commit()
    return True


def get_conflict_group_members(
    *,
    session: Session,
    group_id: uuid.UUID
) -> list[TraitConflictGroupMember]:
    """Get all trait members of a conflict group."""
    return list(session.exec(
        select(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.group_id == group_id)
    ).all())


def get_trait_conflict_memberships(
    *,
    session: Session,
    trait_id: uuid.UUID
) -> list[TraitConflictGroup]:
    """Get all conflict groups that contain a specific trait."""
    return list(session.exec(
        select(TraitConflictGroup)
        .join(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.trait_id == trait_id)
    ).all())


# =============================================================================
# CONFLICT VALIDATION
# =============================================================================

def check_trait_conflicts(
    *,
    session: Session,
    persona_id: uuid.UUID,
    new_trait_id: uuid.UUID
) -> list[dict]:
    """
    Check if adding a trait to a persona would create a logical conflict.
    Returns list of conflicts found, empty list if no conflicts.
    """
    # Get all conflict groups that include the new trait
    conflict_groups = session.exec(
        select(TraitConflictGroup)
        .join(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.trait_id == new_trait_id)
    ).all()

    if not conflict_groups:
        return []

    # Get persona's current trait IDs
    current_trait_ids = {
        link.trait_id for link in
        session.exec(
            select(PersonaTraitLink)
            .where(PersonaTraitLink.persona_id == persona_id)
        ).all()
    }

    conflicts = []
    for group in conflict_groups:
        # Get all trait IDs in this conflict group
        group_trait_ids = {
            member.trait_id for member in
            session.exec(
                select(TraitConflictGroupMember)
                .where(TraitConflictGroupMember.group_id == group.id)
            ).all()
        }

        # Check for overlap with current traits (excluding the new trait)
        conflicting_traits = current_trait_ids & group_trait_ids

        if conflicting_traits:
            conflicts.append({
                "group_id": str(group.id),
                "group_name": group.name,
                "conflict_type": group.conflict_type,
                "reason": group.reason,
                "conflicting_trait_ids": [str(tid) for tid in conflicting_traits]
            })

    return conflicts


def check_archetype_trait_conflicts(
    *,
    session: Session,
    archetype_id: uuid.UUID,
    new_trait_id: uuid.UUID
) -> list[dict]:
    """
    Check if adding a trait to an archetype would create a logical conflict.
    Similar to persona check but uses ArchetypeTraitLink.
    """
    conflict_groups = session.exec(
        select(TraitConflictGroup)
        .join(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.trait_id == new_trait_id)
    ).all()

    if not conflict_groups:
        return []

    current_trait_ids = {
        link.trait_id for link in
        session.exec(
            select(ArchetypeTraitLink)
            .where(ArchetypeTraitLink.archetype_id == archetype_id)
        ).all()
    }

    conflicts = []
    for group in conflict_groups:
        group_trait_ids = {
            member.trait_id for member in
            session.exec(
                select(TraitConflictGroupMember)
                .where(TraitConflictGroupMember.group_id == group.id)
            ).all()
        }

        conflicting_traits = current_trait_ids & group_trait_ids

        if conflicting_traits:
            conflicts.append({
                "group_id": str(group.id),
                "group_name": group.name,
                "conflict_type": group.conflict_type,
                "reason": group.reason,
                "conflicting_trait_ids": [str(tid) for tid in conflicting_traits]
            })

    return conflicts


def validate_conflict_group_cardinality(
    *,
    session: Session,
    group_id: uuid.UUID
) -> dict:
    """
    Validate that a conflict group has appropriate member count for its type.
    Returns validation result with any warnings/errors.
    """
    group = session.get(TraitConflictGroup, group_id)
    if not group:
        return {"valid": False, "error": "Group not found"}

    members = get_conflict_group_members(session=session, group_id=group_id)
    member_count = len(members)

    result = {
        "valid": True,
        "group_id": str(group_id),
        "conflict_type": group.conflict_type,
        "member_count": member_count,
        "warnings": [],
        "errors": []
    }

    if group.conflict_type == "contradictory":
        if member_count < 2:
            result["errors"].append("Contradictory requires exactly 2 traits")
            result["valid"] = False
        elif member_count > 2:
            result["warnings"].append(
                f"Contradictory typically has exactly 2 traits, found {member_count}"
            )
    else:  # contrary or subcontrary
        if member_count < 2:
            result["errors"].append(f"{group.conflict_type} requires at least 2 traits")
            result["valid"] = False

    return result
```

---

## Routes (for app/api/routes/trait_conflicts.py)

```python
"""
Trait Conflict Routes - Logical Contradiction Management

Handles creating and managing trait conflict groups for Carroll logic implementation.

Endpoints:
- GET    /trait-conflicts                     - List all conflict groups
- GET    /trait-conflicts/{group_id}          - Get single conflict group
- GET    /trait-conflicts/{group_id}/members  - Get members of a group
- POST   /trait-conflicts                     - Create new conflict group
- PUT    /trait-conflicts/{group_id}          - Update conflict group
- DELETE /trait-conflicts/{group_id}          - Delete conflict group
- POST   /trait-conflicts/{group_id}/members  - Add trait to group
- DELETE /trait-conflicts/{group_id}/members/{trait_id} - Remove trait from group
- GET    /trait-conflicts/check/persona/{persona_id}     - Check conflicts for persona
- GET    /trait-conflicts/check/archetype/{archetype_id} - Check conflicts for archetype
- GET    /trait-conflicts/by-trait/{trait_id} - Get groups containing a trait
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    TraitConflictGroup,
    TraitConflictGroupCreate,
    TraitConflictGroupUpdate,
    TraitConflictGroupPublic,
    TraitConflictGroupsPublic,
    TraitConflictGroupMember,
    TraitConflictGroupMemberCreate,
    TraitConflictGroupMemberPublic,
    TraitConflictGroupMembersPublic,
    Message,
)
from app import crud

router = APIRouter(prefix="/trait-conflicts", tags=["trait-conflicts"])


# =============================================================================
# CONFLICT GROUP ENDPOINTS
# =============================================================================

@router.get("/", response_model=TraitConflictGroupsPublic)
def read_trait_conflict_groups(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    conflict_type: str | None = Query(
        default=None,
        description="Filter by conflict type: contradictory, contrary, subcontrary"
    )
) -> Any:
    """
    Retrieve trait conflict groups with optional filtering.
    """
    groups, count = crud.get_trait_conflict_groups(
        session=session,
        skip=skip,
        limit=limit,
        conflict_type=conflict_type
    )
    return TraitConflictGroupsPublic(data=groups, count=count)


@router.get("/{group_id}", response_model=TraitConflictGroupPublic)
def read_trait_conflict_group(
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID
) -> Any:
    """
    Get a trait conflict group by ID.
    """
    group = crud.get_trait_conflict_group(session=session, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Conflict group not found")
    return group


@router.post("/", response_model=TraitConflictGroupPublic)
def create_trait_conflict_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_in: TraitConflictGroupCreate
) -> Any:
    """
    Create a new trait conflict group.

    Optionally include trait_ids to add initial members.

    conflict_type must be one of:
    - contradictory: Exactly one trait must be true (binary, e.g., Mortal/Immortal)
    - contrary: At most one trait can be true (n-ary, e.g., Hot/Warm/Cold)
    - subcontrary: At least one trait must be true
    """
    try:
        group = crud.create_trait_conflict_group(session=session, group_in=group_in)
        return group
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{group_id}", response_model=TraitConflictGroupPublic)
def update_trait_conflict_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
    group_in: TraitConflictGroupUpdate
) -> Any:
    """
    Update a trait conflict group.
    """
    group = crud.get_trait_conflict_group(session=session, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Conflict group not found")

    try:
        updated = crud.update_trait_conflict_group(
            session=session,
            db_group=group,
            group_in=group_in
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{group_id}")
def delete_trait_conflict_group(
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID
) -> Message:
    """
    Delete a trait conflict group and all its members.
    """
    deleted = crud.delete_trait_conflict_group(session=session, group_id=group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conflict group not found")
    return Message(message="Conflict group deleted successfully")


# =============================================================================
# CONFLICT GROUP MEMBER ENDPOINTS
# =============================================================================

@router.get("/{group_id}/members", response_model=TraitConflictGroupMembersPublic)
def read_conflict_group_members(
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID
) -> Any:
    """
    Get all trait members of a conflict group.
    """
    group = crud.get_trait_conflict_group(session=session, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Conflict group not found")

    members = crud.get_conflict_group_members(session=session, group_id=group_id)
    return TraitConflictGroupMembersPublic(data=members, count=len(members))


@router.post("/{group_id}/members", response_model=TraitConflictGroupMemberPublic)
def add_trait_to_conflict_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
    member_in: TraitConflictGroupMemberCreate
) -> Any:
    """
    Add a trait to a conflict group.
    """
    try:
        member = crud.add_trait_to_conflict_group(
            session=session,
            group_id=group_id,
            member_in=member_in
        )
        return member
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{group_id}/members/{trait_id}")
def remove_trait_from_conflict_group(
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
    trait_id: uuid.UUID
) -> Message:
    """
    Remove a trait from a conflict group.
    """
    removed = crud.remove_trait_from_conflict_group(
        session=session,
        group_id=group_id,
        trait_id=trait_id
    )
    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Trait not found in this conflict group"
        )
    return Message(message="Trait removed from conflict group")


# =============================================================================
# CONFLICT CHECKING ENDPOINTS
# =============================================================================

@router.get("/check/persona/{persona_id}")
def check_persona_trait_conflicts(
    session: SessionDep,
    current_user: CurrentUser,
    persona_id: uuid.UUID,
    trait_id: uuid.UUID = Query(description="Trait ID to check for conflicts")
) -> Any:
    """
    Check if adding a trait to a persona would create a logical conflict.

    Returns list of conflicts if any exist, empty list if safe to add.
    """
    conflicts = crud.check_trait_conflicts(
        session=session,
        persona_id=persona_id,
        new_trait_id=trait_id
    )
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
        "can_add_trait": len(conflicts) == 0
    }


@router.get("/check/archetype/{archetype_id}")
def check_archetype_trait_conflicts(
    session: SessionDep,
    current_user: CurrentUser,
    archetype_id: uuid.UUID,
    trait_id: uuid.UUID = Query(description="Trait ID to check for conflicts")
) -> Any:
    """
    Check if adding a trait to an archetype would create a logical conflict.

    Returns list of conflicts if any exist, empty list if safe to add.
    """
    conflicts = crud.check_archetype_trait_conflicts(
        session=session,
        archetype_id=archetype_id,
        new_trait_id=trait_id
    )
    return {
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
        "can_add_trait": len(conflicts) == 0
    }


@router.get("/by-trait/{trait_id}", response_model=TraitConflictGroupsPublic)
def get_conflict_groups_by_trait(
    session: SessionDep,
    current_user: CurrentUser,
    trait_id: uuid.UUID
) -> Any:
    """
    Get all conflict groups that contain a specific trait.

    Useful for understanding what conflicts a trait participates in.
    """
    groups = crud.get_trait_conflict_memberships(session=session, trait_id=trait_id)
    return TraitConflictGroupsPublic(data=groups, count=len(groups))


@router.get("/{group_id}/validate")
def validate_conflict_group(
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID
) -> Any:
    """
    Validate that a conflict group has appropriate member count for its type.

    - contradictory: Should have exactly 2 members
    - contrary/subcontrary: Should have at least 2 members
    """
    result = crud.validate_conflict_group_cardinality(
        session=session,
        group_id=group_id
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
```

---

## Router Registration (for app/api/main.py)

Add this import and registration:

```python
from app.api.routes import trait_conflicts

# In the router includes section:
api_router.include_router(trait_conflicts.router)
```

---

## Migration Notes

When adding to `models.py`:

1. Add the model classes in the appropriate section
2. Add relationship bindings at the end of the file (post-definition pattern)
3. Create migration: `alembic revision --autogenerate -m "Add TraitConflictGroup and TraitConflictGroupMember"`
4. Apply migration: `alembic upgrade head`
5. Add CRUD operations to `crud.py`
6. Create routes in `app/api/routes/trait_conflicts.py`
7. Register router in `app/api/main.py`

---

## Conflict Type Reference

| Type | Definition | Cardinality | Example |
|------|------------|-------------|---------|
| `contradictory` | Exactly one must be true | 2 | Mortal/Immortal |
| `contrary` | At most one can be true | 2+ | Hot/Warm/Cold |
| `subcontrary` | At least one must be true | 2+ | Some X / Some not-X |
