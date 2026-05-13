# Phase 5 Model Definition Addendum
**Purpose:** ProgressSnapshot model following data-model-best-practices.md pattern
**Date:** 2026-01-04

---

## Update to Step 1.1: Add ProgressSnapshot Model

**Note:** This addendum follows the pattern from `docs/data-model-best-practices.md` for relationship definitions.

### 1. Define ProgressSnapshot Model (Fields Only)

Add to `backend/app/models.py` in the appropriate section:

```python
# ==================== ProgressSnapshot Models (PHASE 5) ====================

class ProgressSnapshotBase(SQLModel):
    """
    Base model for progress snapshots.

    Snapshots are performance optimization - cached replayed state
    at specific head positions to avoid replaying from root.
    """
    story_state: dict[str, Any] = Field(sa_column=Column(JSON))
    current_node_id: uuid.UUID


class ProgressSnapshotCreate(ProgressSnapshotBase):
    """Input model for creating snapshot"""
    progress_id: uuid.UUID
    choice_id: uuid.UUID


class ProgressSnapshotUpdate(SQLModel):
    """Update model for ProgressSnapshot (rarely used)"""
    story_state: dict[str, Any] | None = Field(default=None)
    current_node_id: uuid.UUID | None = Field(default=None)


class ProgressSnapshot(ProgressSnapshotBase, table=True):
    """
    Database model for progress state snapshots.

    Created every N choices to optimize replay performance.
    Replay can start from nearest snapshot instead of root.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    progress_id: uuid.UUID = Field(
        foreign_key="userstoryprogress.id",
        nullable=False,
        ondelete="CASCADE",
    )
    choice_id: uuid.UUID = Field(
        foreign_key="usernodechoice.id",
        nullable=False,
        description="Head position of this snapshot",
    )

    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships added via post-definition binding (see end of models.py)


class ProgressSnapshotPublic(ProgressSnapshotBase):
    """Public API response model for ProgressSnapshot"""
    id: uuid.UUID
    progress_id: uuid.UUID
    choice_id: uuid.UUID
    created_at: datetime


class ProgressSnapshotsPublic(SQLModel):
    """Collection response for ProgressSnapshots"""
    data: list[ProgressSnapshotPublic]
    count: int
```

### ⚠️ Critical Note: No Relationship Type Hints in Table Models

**DO NOT** add relationship type hints like this in the table model:
```python
# ❌ WRONG - causes TypeError in SQLModel
class ProgressSnapshot(ProgressSnapshotBase, table=True):
    progress: "UserStoryProgress | None" = None  # DON'T DO THIS
    choice: "UserNodeChoice | None" = None       # DON'T DO THIS
```

**Why?** When `table=True`, SQLModel processes ALL class attributes as potential database columns. Relationship type hints confuse SQLModel's column detection, causing:
```
TypeError: issubclass() arg 1 must be a class
```

**Correct Approach:** Define relationships ONLY via post-definition binding (see below).

### 2. Post-Definition Relationship Binding

Add at the **END** of `backend/app/models.py` (after all model definitions):

```python
# ==================== Post-Definition Relationships (PHASE 5) ====================
# Following pattern from docs/data-model-best-practices.md

# ProgressSnapshot → UserStoryProgress (many-to-one)
ProgressSnapshot.progress = Relationship(
    back_populates="snapshots",
    sa_relationship_kwargs={"lazy": "joined"}
)

# ProgressSnapshot → UserNodeChoice (many-to-one)
ProgressSnapshot.choice = Relationship(
    back_populates="snapshots",
    sa_relationship_kwargs={"lazy": "joined"}
)

# UserStoryProgress → ProgressSnapshot (one-to-many, reverse)
UserStoryProgress.snapshots = Relationship(
    back_populates="progress",
    sa_relationship_kwargs={
        "cascade": "all, delete-orphan",
        "lazy": "select"
    }
)

# UserNodeChoice → ProgressSnapshot (one-to-many, reverse)
UserNodeChoice.snapshots = Relationship(
    back_populates="choice",
    sa_relationship_kwargs={
        "cascade": "all, delete-orphan",
        "lazy": "select"
    }
)
```

### Why This Pattern?

1. **Forward References**: Type hints use strings (`"UserStoryProgress"`) to avoid circular import issues
2. **Post-Definition Binding**: Relationships added after all models exist (best practice)
3. **Bidirectional**: Both forward (ProgressSnapshot → Progress) and reverse (Progress → Snapshots)
4. **Cascade Behavior**: Deleting progress/choice deletes snapshots automatically
5. **Lazy Loading**: `joined` for FK, `select` for collections (performance optimization)

### Migration Notes

The Alembic migration will correctly detect:
- ✅ `progresssnapshot` table creation
- ✅ Foreign keys to `userstoryprogress` and `usernodechoice`
- ✅ All columns with correct types and constraints

Relationships are ORM-level only and don't affect schema migration.

---

## Quick Checklist

- [X] Add ProgressSnapshot models to `models.py` (fields only)
- [X] Add post-definition relationship bindings at END of `models.py`
- [X] Run `alembic revision --autogenerate -m "Add ProgressSnapshot model"`
- [X] Review migration file for correctness (aa244f8bb6c0)
- [X] Run `alembic upgrade head`
- [X] Verify relationships work: `progress.snapshots` and `snapshot.progress`

---

**See Also:**
- docs/data-model-best-practices.md - Relationship pattern details
- backend/app/models.py - Current model definitions
- CYOA_PHASE5_QUICKREF.md - Full Phase 5 implementation guide
