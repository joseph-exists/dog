# CYOA Event Model Migration Plan

**Last Updated:** 2026-01-04
**Status:** 🔄 Design Document
**Purpose:** Bridge current STORY_SYSTEM to event-sourced branching timeline model

---

## Executive Summary

This document outlines the **minimal set of changes** needed to evolve the current story system into an event-sourced CYOA engine with branching timelines and rewind capability, as specified in `CYOA.md` and `MVP event model outline.md`.

### Current State vs. Target State

| Aspect | Current STORY_SYSTEM | Target CYOA Model |
|--------|---------------------|-------------------|
| **State Model** | Mutable `story_state` dict | Immutable event stream + projections |
| **Timeline** | Linear progression only | Branching tree with rewind |
| **History** | Append-only `UserNodeChoice` | Tree-structured events with parent pointers |
| **Replay** | No replay (state is truth) | Events are truth, state is derived |
| **Undo** | Not supported | Jump to ancestor node |
| **Concurrency** | No version control | Optimistic concurrency on `head_version` |
| **Real-time** | Not supported | WebSocket + Redis pub/sub |
| **Determinism** | N/A (no replay) | RNG outcomes captured in events |

### Migration Strategy

**Phased approach to minimize disruption:**
1. **Phase 1:** Add event tree structure (backward compatible)
2. **Phase 2:** Add head pointer and replay logic
3. **Phase 3:** Add undo/rewind APIs
4. **Phase 4:** Add real-time distribution
5. **Phase 5:** Deprecate mutable state updates

---

## []  Phase 1: Event Tree Foundation

### Goal
Transform `UserNodeChoice` from append-only log to tree structure without breaking existing APIs.

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

### Backward Compatibility

**Existing APIs continue to work:**
- `POST /user-personas/{id}/stories/{story_id}/choices/{choice_id}` appends choice with `parent_choice_id = current_head`
- `GET /user-personas/{id}/stories/{story_id}/current-node` reads from `current_node_id` (unchanged)
- `story_state` is still updated mutably (Phase 1 doesn't change this yet)

**New behavior:**
- Each new choice automatically sets `parent_choice_id` to previous `head_choice_id`
- `head_choice_id` and `head_version` are updated atomically with choice creation
- Tree structure exists but undo/rewind not exposed yet

---
## Relationship Definition Validation

### Problem: Missing Post-Definition Binding

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
```

## Phase 2: Replay & Projection Logic

### Goal
Add ability to reconstruct `story_state` from event chain (root → head).

### New CRUD Functions

#### 2.1 Get Ancestor Chain

```python
def get_choice_ancestor_chain(
    *, session: Session, choice_id: uuid.UUID
) -> list[UserNodeChoice]:
    """
    Returns ancestor chain from root to specified choice (inclusive).
    Used for replay and timeline display.

    Returns: [root_choice, ..., parent_choice, choice_id]
    """
    chain = []
    current_id = choice_id

    while current_id is not None:
        choice = session.get(UserNodeChoice, current_id)
        if not choice:
            break
        chain.append(choice)
        current_id = choice.parent_choice_id

    return list(reversed(chain))  # Root → head order
```

#### 2.2 Replay State from Head

```python
def replay_state_from_head(
    *,
    session: Session,
    progress_id: uuid.UUID,
    head_choice_id: uuid.UUID | None
) -> dict[str, Any]:
    """
    Reconstruct story_state by replaying all events from root to head.

    This is the SOURCE OF TRUTH for state in event-sourced model.
    The UserStoryProgress.story_state field becomes a denormalized cache.

    Returns: Reconstructed state dict
    """
    if head_choice_id is None:
        return {}  # At story start

    # Get all events from root to head
    chain = get_choice_ancestor_chain(session=session, choice_id=head_choice_id)

    # Replay events (shallow merge)
    state = {}
    for choice in chain:
        if choice.state_changes:
            state.update(choice.state_changes)

    return state
```

#### 2.3 Get Current Node from Head

```python
def get_current_node_from_head(
    *, session: Session, head_choice_id: uuid.UUID | None, story_id: uuid.UUID, story_version: int
) -> uuid.UUID:
    """
    Derive current_node_id from head position.

    If head_choice_id is None, return start node.
    Otherwise, return to_node_id of head choice.
    """
    if head_choice_id is None:
        # At story start - find start node
        statement = select(StoryNode).where(
            StoryNode.story_id == story_id,
            StoryNode.story_version == story_version,
            StoryNode.is_start_node == True
        )
        start_node = session.exec(statement).first()
        if not start_node:
            raise ValueError(f"No start node for story {story_id} v{story_version}")
        return start_node.id

    # Return destination of head choice
    choice = session.get(UserNodeChoice, head_choice_id)
    return choice.to_node_id
```

### Modified API Endpoints

#### 2.2 Update Choice Endpoint (Event Append)

```python
@router.post("/{story_id}/choices/{choice_id}", response_model=UserStoryProgressPublic)
def make_story_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    choice_id: uuid.UUID,
) -> Any:
    """
    MODIFIED: Append choice as child of current head (tree structure).
    """
    # ... existing validation ...

    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )

    # NEW: Optimistic concurrency check (optional in Phase 2)
    # expected_version = request.headers.get("If-Match")
    # if expected_version and int(expected_version) != progress.head_version:
    #     raise HTTPException(status_code=409, detail="Head version conflict")

    # Create choice with parent pointer
    user_choice = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=progress.head_choice_id,  # NEW: Link to parent
        choice_text=choice.text,
        from_node_id=choice.from_node_id,
        to_node_id=choice.to_node_id,
        state_changes=choice.sets_state,
        rng_data=None  # TODO: Capture RNG outcomes if applicable
    )
    session.add(user_choice)
    session.flush()  # Get ID

    # Update head pointer (atomic move)
    progress.head_choice_id = user_choice.id
    progress.head_version += 1
    progress.current_node_id = choice.to_node_id

    # TRANSITION: Still update story_state mutably for backward compat
    # In Phase 5, this becomes: progress.story_state = replay_state_from_head(...)
    if choice.sets_state:
        if progress.story_state:
            progress.story_state.update(choice.sets_state)
        else:
            progress.story_state = choice.sets_state

    # Check end node
    to_node = session.get(StoryNode, choice.to_node_id)
    if to_node and to_node.is_end_node:
        progress.is_completed = True

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

---

## Phase 3: Undo & Rewind APIs

### Goal
Expose timeline navigation (jump to ancestor, undo).

### New API Endpoints

#### 3.1 Undo (Jump to Parent)
#### 

```python
@router.post("/{story_id}/undo", response_model=UserStoryProgressPublic)
def undo_last_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Move head to parent choice (rewind one step).

    Behavior:
    - Moves head_choice_id to parent of current head
    - Increments head_version (optimistic lock)
    - Replays state from new head
    - Old future remains in database but becomes hidden

    Returns: Updated progress
    """
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    if progress.head_choice_id is None:
        raise HTTPException(status_code=400, detail="Already at story start, cannot undo")

    # Get parent choice
    current_choice = session.get(UserNodeChoice, progress.head_choice_id)
    if not current_choice:
        raise HTTPException(status_code=500, detail="Head choice not found (data corruption)")

    # Move head to parent
    progress.head_choice_id = current_choice.parent_choice_id
    progress.head_version += 1

    # Replay state from new head
    progress.story_state = replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Update current node
    progress.current_node_id = get_current_node_from_head(
        session=session,
        head_choice_id=progress.head_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version
    )

    # Reset completion flag if needed
    progress.is_completed = False

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

#### 3.2 Jump to Ancestor

```python
class JumpRequest(SQLModel):
    choice_id: uuid.UUID | None  # null = jump to start
    expected_head_version: int  # Optimistic concurrency


@router.post("/{story_id}/jump", response_model=UserStoryProgressPublic)
def jump_to_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    jump_request: JumpRequest,
) -> Any:
    """
    Jump head to any ancestor choice (rewind to arbitrary point).

    Validation:
    - Target choice must be ancestor of current head (enforces no forward jumps)
    - Optimistic concurrency via expected_head_version

    Behavior:
    - Moves head_choice_id to target
    - Replays state from target
    - All future choices after target become hidden

    Returns: Updated progress
    """
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    # Optimistic concurrency check
    if jump_request.expected_head_version != progress.head_version:
        raise HTTPException(
            status_code=409,
            detail=f"Head version conflict: expected {jump_request.expected_head_version}, got {progress.head_version}"
        )

    target_choice_id = jump_request.choice_id

    # Validate target is ancestor of current head
    if target_choice_id is not None:
        # Check target exists
        target_choice = session.get(UserNodeChoice, target_choice_id)
        if not target_choice or target_choice.progress_id != progress.id:
            raise HTTPException(status_code=404, detail="Target choice not found")

        # Verify target is ancestor of current head
        ancestors = get_choice_ancestor_chain(session=session, choice_id=progress.head_choice_id)
        ancestor_ids = [c.id for c in ancestors]

        if target_choice_id not in ancestor_ids:
            raise HTTPException(
                status_code=400,
                detail="Target choice is not an ancestor of current head (forward jumps not allowed)"
            )

    # Move head to target
    progress.head_choice_id = target_choice_id
    progress.head_version += 1

    # Replay state from new head
    progress.story_state = replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Update current node
    progress.current_node_id = get_current_node_from_head(
        session=session,
        head_choice_id=progress.head_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version
    )

    # Reset completion flag
    progress.is_completed = False

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

#### 3.3 Get Timeline (Breadcrumb Trail)

```python
class TimelineEvent(SQLModel):
    """Timeline entry for UI breadcrumbs."""
    choice_id: uuid.UUID | None
    choice_text: str
    node_title: str
    choice_time: datetime
    is_current: bool


class Timeline(SQLModel):
    """Active timeline from root → head."""
    events: list[TimelineEvent]
    head_version: int


@router.get("/{story_id}/timeline", response_model=Timeline)
def get_timeline(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Get active timeline (root → head) for breadcrumb UI.

    Returns ONLY the ancestor chain, never siblings or abandoned branches.
    """
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    # Get start node
    start_node = session.exec(
        select(StoryNode).where(
            StoryNode.story_id == story_id,
            StoryNode.story_version == progress.story_version,
            StoryNode.is_start_node == True
        )
    ).first()

    events = [
        TimelineEvent(
            choice_id=None,
            choice_text="Story Start",
            node_title=start_node.title if start_node else "Unknown",
            choice_time=progress.started_at,
            is_current=(progress.head_choice_id is None)
        )
    ]

    # Add ancestor chain
    if progress.head_choice_id:
        chain = get_choice_ancestor_chain(
            session=session, choice_id=progress.head_choice_id
        )

        for choice in chain:
            node = session.get(StoryNode, choice.to_node_id)
            events.append(
                TimelineEvent(
                    choice_id=choice.id,
                    choice_text=choice.choice_text,
                    node_title=node.title if node else "Unknown",
                    choice_time=choice.choice_time,
                    is_current=(choice.id == progress.head_choice_id)
                )
            )

    return Timeline(events=events, head_version=progress.head_version)
```

---

## Phase 4: Real-Time Distribution

NOT DOCUMENTED HERE.  SEE CYOA_MIGRATION_ADDENDUM FOR CHANGES.  NO OUTBOX PATTERN AT THIS TIME.


---

## Phase 5: Full Event Sourcing

### Goal
Make `story_state` fully derived (read-only projection).

### Changes

#### 5.1 Remove Mutable State Updates

```python
@router.post("/{story_id}/choices/{choice_id}", response_model=UserStoryProgressPublic)
def make_story_choice(...) -> Any:
    """
    FINAL: story_state is ALWAYS derived from replay, never mutated.
    """
    # ... create user_choice ...

    # Update head pointer
    progress.head_choice_id = user_choice.id
    progress.head_version += 1

    # REMOVED: Manual state update
    # if choice.sets_state:
    #     progress.story_state.update(choice.sets_state)

    # NEW: Always replay
    progress.story_state = replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    progress.current_node_id = get_current_node_from_head(
        session=session,
        head_choice_id=progress.head_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version
    )

    # ... rest unchanged ...
```

#### 5.2 Add Snapshotting (Performance Optimization)

```python
class ProgressSnapshot(SQLModel, table=True):
    """
    Performance optimization: Cache replayed state at specific head positions.
    Used to avoid replaying from root when timeline is long.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    progress_id: uuid.UUID = Field(foreign_key="userstoryprogress.id", nullable=False, ondelete="CASCADE")
    choice_id: uuid.UUID = Field(
        foreign_key="usernodechoice.id",
        description="Head position of this snapshot"
    )

    # Cached state
    story_state: dict[str, Any] = Field(sa_column=Column(JSON))
    current_node_id: uuid.UUID

    created_at: datetime = Field(default_factory=datetime.now)


def replay_state_from_head_optimized(
    *, session: Session, progress_id: uuid.UUID, head_choice_id: uuid.UUID | None
) -> dict[str, Any]:
    """
    Optimized replay using snapshots.

    Logic:
    1. Find nearest snapshot at/before head
    2. Replay events from snapshot → head
    3. If no snapshot, replay from root
    """
    if head_choice_id is None:
        return {}

    # Find nearest snapshot
    ancestor_chain = get_choice_ancestor_chain(session=session, choice_id=head_choice_id)
    ancestor_ids = [c.id for c in ancestor_chain]

    snapshot_stmt = select(ProgressSnapshot).where(
        ProgressSnapshot.progress_id == progress_id,
        ProgressSnapshot.choice_id.in_(ancestor_ids)
    ).order_by(ProgressSnapshot.created_at.desc()).limit(1)

    snapshot = session.exec(snapshot_stmt).first()

    if snapshot:
        # Replay from snapshot
        state = snapshot.story_state.copy()
        snapshot_idx = next(i for i, c in enumerate(ancestor_chain) if c.id == snapshot.choice_id)

        for choice in ancestor_chain[snapshot_idx + 1:]:
            if choice.state_changes:
                state.update(choice.state_changes)
    else:
        # No snapshot, replay from root
        state = {}
        for choice in ancestor_chain:
            if choice.state_changes:
                state.update(choice.state_changes)

    return state


def create_snapshot_if_needed(
    *, session: Session, progress: UserStoryProgress
) -> None:
    """
    Create snapshot every N choices (e.g., every 10 choices).
    """
    SNAPSHOT_INTERVAL = 10

    if progress.head_choice_id is None:
        return

    chain_length = len(get_choice_ancestor_chain(
        session=session, choice_id=progress.head_choice_id
    ))

    if chain_length % SNAPSHOT_INTERVAL == 0:
        snapshot = ProgressSnapshot(
            progress_id=progress.id,
            choice_id=progress.head_choice_id,
            story_state=progress.story_state,
            current_node_id=progress.current_node_id
        )
        session.add(snapshot)
```

---

## Key Design Decisions

### 1. Tree Structure via Parent Pointers

**Choice:** Use `parent_choice_id` foreign key in `UserNodeChoice`

**Rationale:**
- Simple to implement (single column addition)
- Efficient ancestor traversal via recursive CTE
- No need for separate tree/graph tables
- Aligns with CYOA.md specification

**Alternative Rejected:** Materialized path or nested sets (too complex for MVP)

### 2. Head Pointer in Progress Record

**Choice:** Store `head_choice_id` + `head_version` in `UserStoryProgress`

**Rationale:**
- Single source of truth for "current reality"
- Enables optimistic concurrency
- Follows event sourcing best practices
- Natural fit for existing data model

**Alternative Rejected:** Separate `heads` table (unnecessary overhead for single-player stories)

### 3. Replay on Read (Phase 2-4) vs. Projection on Write (Phase 5)

**Choice:** Initially keep mutable updates, transition to pure replay

**Rationale:**
- Phased migration reduces risk
- Backward compatibility during transition
- Performance testing before committing to full event sourcing
- Can add snapshots once replay patterns are validated

**Alternative:** Immediate full event sourcing (higher risk, more disruptive)

### 4. Outbox Pattern for Real-Time

**Choice:** Transactional outbox + background publisher

**Rationale:**
- Atomic consistency (event + notification in same transaction)
- Reliable delivery (retries on failure)
- Industry standard pattern for event sourcing + pub/sub
- Decouples write path from Redis availability

**Alternative Rejected:** Direct Redis publish in request handler (dual-write problem)

---

## Migration Checklist

### Phase 1: Foundation (Week 1)
- [ ] Add `parent_choice_id` to `UserNodeChoice` model
- [ ] Add `rng_data` to `UserNodeChoice` model
- [ ] Add `head_choice_id` and `head_version` to `UserStoryProgress`
- [ ] Run database migrations
- [ ] Update `make_story_choice` to set `parent_choice_id`
- [ ] Add tests for tree structure creation
- [ ] Backfill `parent_choice_id` for existing choices (set to previous choice by time)

### Phase 2: Replay (Week 2)
- [ ] Implement `get_choice_ancestor_chain()`
- [ ] Implement `replay_state_from_head()`
- [ ] Implement `get_current_node_from_head()`
- [ ] Add tests for replay correctness
- [ ] Add performance benchmarks (replay vs. mutable)
- [ ] Document replay semantics

### Phase 3: Undo/Rewind (Week 3)
- [ ] Implement `POST /{story_id}/undo` endpoint
- [ ] Implement `POST /{story_id}/jump` endpoint
- [ ] Implement `GET /{story_id}/timeline` endpoint
- [ ] Add optimistic concurrency checks (`expected_head_version`)
- [ ] Add tests for undo/jump validation
- [ ] Add tests for abandoned branch hiding

### Phase 4: Real-Time (Week 4)
- [ ] Set up Redis connection
- [ ] Create `Outbox` model and migration
- [ ] Implement outbox publisher background worker
- [ ] Add WebSocket endpoint (`/stories/{id}/stream`)
- [ ] Modify choice endpoint to write outbox events
- [ ] Modify undo/jump endpoints to write outbox events
- [ ] Add WebSocket connection tests
- [ ] Add Redis failover handling

### Phase 5: Full Event Sourcing (Week 5)
- [ ] Remove mutable state updates from choice endpoint
- [ ] Implement `ProgressSnapshot` model
- [ ] Implement `replay_state_from_head_optimized()`
- [ ] Add snapshot creation logic (every N choices)
- [ ] Benchmark replay performance with/without snapshots
- [ ] Deprecate direct `story_state` mutations
- [ ] Update documentation

---

## Testing Strategy

### Unit Tests

```python
def test_choice_creates_tree_structure():
    """Verify parent_choice_id links are created correctly."""

def test_ancestor_chain_traversal():
    """Verify ancestor chain returns correct order (root → head)."""

def test_replay_state_correctness():
    """Verify replayed state matches expected state."""

def test_undo_moves_head_to_parent():
    """Verify undo updates head_choice_id correctly."""

def test_jump_validates_ancestor():
    """Verify jump rejects non-ancestor targets."""

def test_abandoned_branch_hidden():
    """Verify timeline API doesn't return abandoned branches."""

def test_head_version_increment():
    """Verify head_version increments on every head move."""
```

### Integration Tests

```python
def test_branching_timeline():
    """
    Scenario:
    1. Make choice A → B
    2. Make choice B → C
    3. Undo to B
    4. Make choice B → D (creates branch)
    5. Verify timeline shows A → B → D (not C)
    """

def test_optimistic_concurrency():
    """
    Scenario:
    1. Two clients load same head_version
    2. Client 1 makes choice (head_version++)
    3. Client 2 makes choice with stale version
    4. Verify client 2 gets 409 conflict
    """

def test_replay_after_multiple_undos():
    """
    Scenario:
    1. Make 10 choices
    2. Undo 5 times
    3. Make 3 new choices
    4. Verify replayed state is correct
    """
```

### Performance Tests

```python
def benchmark_replay_vs_mutable():
    """Compare replay performance vs. mutable state updates."""

def benchmark_replay_with_snapshots():
    """Measure snapshot effectiveness (10, 50, 100 choice chains)."""

def benchmark_ancestor_chain_query():
    """Measure query performance for deep trees (100+ choices)."""
```

---

## Risks & Mitigations

### Risk 1: Replay Performance

**Risk:** Replaying long chains (100+ choices) may be slow

**Mitigation:**
- Add snapshots in Phase 5
- Monitor replay times, optimize if needed
- Consider denormalized projection table if snapshots insufficient

### Risk 2: Concurrent Modifications

**Risk:** Multiple clients making choices simultaneously causes conflicts

**Mitigation:**
- Use optimistic concurrency (`head_version` check)
- Return 409 Conflict with latest state
- Frontend retries with updated version

### Risk 3: Orphaned Branches

**Risk:** Abandoned branches accumulate, wasting storage

**Mitigation:**
- Add cleanup job to archive/delete old abandoned branches
- Document retention policy (e.g., keep 30 days)
- Add metrics to monitor branch growth

### Risk 4: Redis Unavailability

**Risk:** Redis failure breaks real-time updates

**Mitigation:**
- Outbox ensures events are persisted (can replay later)
- Clients refetch state on reconnect
- Redis is optional enhancement, not critical path

---

## Success Metrics

### Functionality
- ✅ Undo works correctly (moves head to parent)
- ✅ Jump validates ancestor constraint
- ✅ Abandoned branches hidden from timeline API
- ✅ Replayed state matches mutable state (during transition)

### Performance
- Replay time < 50ms for 100-choice chain (without snapshots)
- Replay time < 10ms for 100-choice chain (with snapshots)
- Undo latency < 100ms
- WebSocket push latency < 200ms

### Reliability
- No state corruption after undo/jump
- Optimistic concurrency prevents silent conflicts
- Outbox ensures eventual delivery of notifications

---

## Open Questions

### Q1: NPC/Agent Randomness

**Question:** How to capture PydanticAI agent responses in `rng_data`?

**Proposed Answer:**
- Store agent response deterministically in `rng_data.agent_outcomes`
- Example: `{"npc_movement": {"npc_id": "bram", "destination": "forest"}}`
- On replay, use stored outcome instead of re-invoking agent

**Needs Discussion:** Agent state synchronization, multi-turn dialogues

### Q2: Snapshot Granularity

**Question:** Every N choices, or event-triggered (e.g., end of chapter)?

**Proposed Answer:**
- Start with simple: every 10 choices
- Monitor performance, adjust threshold
- Future: Let authors mark "snapshot points" in story

### Q3: Branch Cleanup Policy

**Question:** When/how to delete abandoned branches?

**Proposed Answer:**
- Keep all branches for 30 days
- After 30 days, offer "compress timeline" option
- Superuser can force cleanup earlier
- Never auto-delete (player may want to explore old branches)

**Needs Discussion:** Legal/compliance implications of data retention

---

## Conclusion

This migration plan provides a **clear, phased path** from the current linear story system to a full event-sourced branching timeline model. Each phase is independently valuable and backward compatible, allowing incremental deployment with minimal risk.

**Total Estimated Effort:** 5 weeks (1 week per phase)
**Complexity:** Medium (builds on existing architecture)
**Impact:** High (enables core CYOA rewind feature)

**Next Steps:**
1. Review this document with team
2. Prototype Phase 1 in feature branch
3. Performance test replay logic before Phase 5 commitment
4. Decide on Redis infrastructure requirements

---

**Questions? Contact backend team or file issue in project repository.**
