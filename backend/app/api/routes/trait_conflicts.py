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