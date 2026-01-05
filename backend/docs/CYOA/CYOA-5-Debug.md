implementation:

lines 24-93 of models.py:
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

    Semantics:
    - Immutable once created (no updates after creation)
    - Each snapshot linked to specific choice_id (head position)
    - Replaying from snapshot: start with snapshot.story_state,
      then apply events from (snapshot.choice_id → target]
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    progress_id: uuid.UUID = Field(
        foreign_key="userstoryprogress.id",
        nullable=False,
        ondelete="CASCADE"
    )
    choice_id: uuid.UUID = Field(
        foreign_key="usernodechoice.id",
        nullable=False,
        description="Head position of this snapshot"
    )

    created_at: datetime = Field(default_factory=datetime.now)


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
lines 2020-2149 of models.py
```python
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