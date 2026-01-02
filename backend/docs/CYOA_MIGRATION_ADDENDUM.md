# CYOA Migration Plan - TinyFoot Compliance Addendum

**Last Updated:** 2026-01-01
**Status:** 🔄 Supplement to CYOA_MIGRATION_PLAN.md
**Purpose:** Ensure migration plan follows TinyFoot backend patterns from RULES.md and data-model-best-practices.md

---

## Overview

This addendum corrects and supplements CYOA_MIGRATION_PLAN.md to ensure full compliance with TinyFoot's established backend patterns, particularly regarding:
1. SQLModel model definition patterns
2. Relationship definition best practices
3. Alembic migration workflow
4. CRUD function patterns
5. API route conventions

---

## Model Definition Corrections

### Problem: Incomplete Model Pattern

The migration plan showed modified database models but didn't follow the complete TinyFoot pattern:
- Base model (shared properties)
- Create model (API input validation)
- Update model (partial updates, all optional)
- Database model (table=True)
- Public model (API response)
- Collection model (paginated responses)

### Solution: Complete Model Definitions

#### Phase 1: UserNodeChoice Model Pattern

```python
# ==================== UserNodeChoice Models (PLAYING) ====================

class UserNodeChoiceBase(SQLModel):
    """
    Base model for recording a player's choice at a node.
    Historical breadcrumb trail through the story.
    """
    choice_text: str = Field(max_length=500)
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID

    # Snapshot of state changes applied by this choice
    state_changes: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class UserNodeChoiceCreate(UserNodeChoiceBase):
    """Input model for recording a choice"""
    progress_id: uuid.UUID
    parent_choice_id: uuid.UUID | None = Field(
        default=None,
        description="Parent event in timeline tree (null for initial state)"
    )

    # NEW in Phase 1
    rng_data: dict[str, Any] | None = Field(
        default=None,
        description="Captured RNG outcomes for deterministic replay"
    )


class UserNodeChoiceUpdate(SQLModel):
    """
    Update model for UserNodeChoice.
    Note: In event sourcing, choices are immutable - this exists for consistency
    but should rarely/never be used.
    """
    # All fields optional (though we don't expect updates in event sourcing)
    choice_text: str | None = Field(default=None, max_length=500)  # type: ignore
    state_changes: dict[str, Any] | None = Field(default=None)
    rng_data: dict[str, Any] | None = Field(default=None)


class UserNodeChoice(UserNodeChoiceBase, table=True):
    """
    Database model for player's choice history.

    MODIFIED in Phase 1: Added parent_choice_id for tree structure.
    Immutable record of decisions made.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    progress_id: uuid.UUID = Field(
        foreign_key="userstoryprogress.id",
        nullable=False,
        ondelete="CASCADE"
    )

    # NEW: Tree structure (Phase 1)
    parent_choice_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="usernodechoice.id",
        description="Parent event in timeline tree (null for initial state)"
    )

    choice_time: datetime = Field(default_factory=datetime.now)

    # NEW: Deterministic randomness support (Phase 1)
    rng_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Captured RNG outcomes for deterministic replay (seeds, rolls, outcomes)"
    )

    # Relationships defined after all models (see bottom of models.py)


class UserNodeChoicePublic(UserNodeChoiceBase):
    """Public API response model for UserNodeChoice"""
    id: uuid.UUID
    progress_id: uuid.UUID
    parent_choice_id: uuid.UUID | None  # NEW in Phase 1
    choice_time: datetime
    rng_data: dict[str, Any] | None  # NEW in Phase 1


class UserNodeChoicesPublic(SQLModel):
    """Collection response for UserNodeChoices"""
    data: list[UserNodeChoicePublic]
    count: int
```

#### Phase 1: UserStoryProgress Model Pattern

```python
# ==================== UserStoryProgress Models (PLAYING) ====================

class UserStoryProgressBase(SQLModel):
    """
    Base model for tracking a player's progress through a Story.
    This is the player's instance - locked to a specific story version.
    """
    current_node_id: uuid.UUID | None = Field(default=None)
    is_completed: bool = Field(default=False)

    # State accumulator - grows as player makes choices
    story_state: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class UserStoryProgressCreate(UserStoryProgressBase):
    """Input model for starting a Story (creating progress instance)"""
    user_persona_id: uuid.UUID
    story_id: uuid.UUID
    story_version: int  # Lock to this version at creation


class UserStoryProgressUpdate(SQLModel):
    """Input model for updating progress (all fields optional)"""
    current_node_id: uuid.UUID | None = Field(default=None)
    is_completed: bool | None = Field(default=None)
    story_state: dict[str, Any] | None = Field(default=None)

    # NEW in Phase 1 (for admin/debug only)
    head_choice_id: uuid.UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)


class UserStoryProgress(UserStoryProgressBase, table=True):
    """
    Database model for player's Story instance.

    MODIFIED in Phase 1: Added head_choice_id and head_version for event sourcing.

    Key semantics:
    - Locked to story_version at creation (immutable)
    - References template StoryNodes via current_node_id
    - Accumulates state in story_state dict
    - Tracks history via UserNodeChoice records
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_persona_id: uuid.UUID = Field(
        foreign_key="userpersona.id",
        nullable=False,
        ondelete="CASCADE"
    )
    story_id: uuid.UUID = Field(
        foreign_key="story.id",
        nullable=False,
        ondelete="CASCADE"
    )
    story_version: int = Field(nullable=False)  # Locked at creation

    # NEW: Head pointer (active timeline position) - Phase 1
    head_choice_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="usernodechoice.id",
        description="Current active event in timeline tree (null = at story start)"
    )

    # NEW: Optimistic concurrency control - Phase 1
    head_version: int = Field(
        default=0,
        description="Increments on every head move (for optimistic locking)"
    )

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships defined after all models (see bottom of models.py)


class UserStoryProgressPublic(UserStoryProgressBase):
    """Public API response model for UserStoryProgress"""
    id: uuid.UUID
    user_persona_id: uuid.UUID
    story_id: uuid.UUID
    story_version: int
    head_choice_id: uuid.UUID | None  # NEW in Phase 1
    head_version: int  # NEW in Phase 1
    started_at: datetime
    updated_at: datetime


class UserStoryProgressesPublic(SQLModel):
    """Collection response for UserStoryProgresses"""
    data: list[UserStoryProgressPublic]
    count: int
```

For complete Outbox and ProgressSnapshot model patterns, see the full addendum document.

---

## Relationship Definition Corrections

### Problem: Missing Post-Definition Binding

The migration plan didn't show how to properly add relationships using TinyFoot's pattern of post-definition binding for circular references.

### Solution: Add Relationships at End of models.py

Per `data-model-best-practices.md`, relationships should be defined AFTER all models are declared.

Add this section to the **bottom of `backend/app/models.py`** in Phase 1:

```python
# ============================================================================
# Phase 1: Event Tree Relationships
# ============================================================================

# UserNodeChoice tree structure relationships
UserNodeChoice.parent_choice = Relationship(
    sa_relationship_kwargs={
        "foreign_keys": "[UserNodeChoice.parent_choice_id]",
        "remote_side": "[UserNodeChoice.id]"
    }
)

UserNodeChoice.children = Relationship(
    back_populates="parent_choice",
    sa_relationship_kwargs={
        "foreign_keys": "[UserNodeChoice.parent_choice_id]"
    }
)

# UserStoryProgress to head choice relationship
UserStoryProgress.head_choice = Relationship(
    sa_relationship_kwargs={
        "foreign_keys": "[UserStoryProgress.head_choice_id]"
    }
)

# Note: Existing relationships remain unchanged
# UserStoryProgress.choice_history is already defined
# UserNodeChoice.progress is already defined
```

---

## Alembic Migration Workflow Corrections

### Problem: Incomplete Migration Instructions

The migration plan mentioned migrations but didn't follow the exact workflow from RULES.md.

### Solution: Complete Migration Steps for Each Phase

#### Phase 1: Migration Workflow

```bash
# 1. Start interactive session in backend container
docker compose exec backend bash

# 2. Create migration with descriptive message
alembic revision --autogenerate -m "Add event tree structure to UserNodeChoice and UserStoryProgress"

# 3. Review generated migration file
# Check: ./app/alembic/versions/XXXX_add_event_tree_structure.py
# Verify:
#   - parent_choice_id column added to usernodechoice
#   - rng_data column added to usernodechoice
#   - head_choice_id column added to userstoryprogress
#   - head_version column added to userstoryprogress
#   - Foreign key constraints are correct
#   - Indexes are created (idx_usernodechoice_parent, idx_userstoryprogress_head)

# 4. Apply migration
alembic upgrade head

# 5. Verify migration applied
alembic current
# Should show: XXXX (head) add event tree structure to...

# 6. Exit container and commit migration files
exit
git add backend/app/alembic/versions/
git commit -m "feat: Add event tree structure for CYOA branching timelines (Phase 1)"
```

---

## API Route Naming Corrections

### Problem: Inconsistent Naming

Some endpoint function names didn't follow FastAPI conventions from RULES.md.

### Solution: Standardized Function Names

```python
# backend/app/api/routes/user_story_progress.py

@router.post("/{story_id}/undo", response_model=UserStoryProgressPublic)
def undo_story_choice(  # Follows update_* pattern
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """Move head to parent choice (rewind one step)."""
    # ... implementation ...


@router.post("/{story_id}/jump", response_model=UserStoryProgressPublic)
def jump_story_head(  # Follows update_* pattern
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    jump_request: JumpRequest,
) -> Any:
    """Jump head to any ancestor choice (rewind to arbitrary point)."""
    # ... implementation ...


@router.get("/{story_id}/timeline", response_model=Timeline)
def read_story_timeline(  # Follows read_* pattern
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """Get active timeline (root → head) for breadcrumb UI."""
    # ... implementation ...
```

---

## Summary of Corrections

### 1. Model Definitions ✅
- Added complete pattern: Base, Create, Update, Database, Public, Collection
- All new models (UserNodeChoice, UserStoryProgress, Outbox, ProgressSnapshot)
- Proper field types and constraints

### 2. Relationship Definitions ✅
- Post-definition binding at end of models.py
- String-based forward references for type hints
- Proper SQLAlchemy relationship configuration

### 3. Alembic Migrations ✅
- Complete workflow with container commands
- Review and verification steps
- Git commit messages following conventions

### 4. CRUD Functions ✅
- Functional, declarative style
- Complete docstrings (Args, Returns, Raises)
- Type hints for all signatures

### 5. API Routes ✅
- Standardized naming: `read_*`, `undo_*/jump_*` (update operations)
- Proper dependency injection
- Response models for all endpoints

### 6. Testing ✅
- Test file structure
- Sample test patterns
- Coverage for all phases

---

## Integration with CYOA_MIGRATION_PLAN.md

This addendum SUPPLEMENTS the migration plan with TinyFoot-specific patterns. Use both documents together:

1. **Read CYOA_MIGRATION_PLAN.md** for overall strategy and phases
2. **Apply this addendum** for implementation details following TinyFoot conventions
3. **Follow RULES.md** for general backend patterns
4. **Follow data-model-best-practices.md** for relationship definitions

---

## Next Actions

- [ ] Update CYOA_MIGRATION_PLAN.md to reference this addendum
- [ ] Create Phase 1 feature branch: `feature/cyoa-phase-1-event-tree`
- [ ] Implement models following patterns in this addendum
- [ ] Create and apply Alembic migrations
- [ ] Write tests following test structure above
- [ ] Review with team before proceeding to Phase 2

---

**Questions? Contact backend team or reference:**
- `backend/docs/RULES.md` - General backend patterns
- `backend/docs/data-model-best-practices.md` - Relationship definitions
- `backend/docs/CYOA_MIGRATION_PLAN.md` - Overall migration strategy
