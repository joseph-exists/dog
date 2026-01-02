# CYOA Phase 5 Quick Reference Card
## Full Event Sourcing (Derived State + Snapshotting)

**Last Updated:** 2026-01-01
**Status:** 🎯 Implementation Guide
**Prerequisites:** ✅ Phase 1, 2, 3, 4 complete
**Estimated Time:** ~12 hours

---

## Overview

Phase 5 completes the migration to full event sourcing by:
- Making `story_state` fully derived (read-only projection from events)
- Removing all mutable state updates
- Adding snapshotting for performance optimization
- Making events the single source of truth

**Key Changes:**
- `UserStoryProgress.story_state` becomes a cached projection
- All state reconstructed via `replay_state_from_head_optimized()`
- Snapshots created every N choices to optimize replay
- Replay latency < 10ms even for 100+ choice chains

---

## Pre-Implementation Checklist

- [ ] Phase 4 complete and tested
- [ ] Replay correctness validated (Phase 2 tests passing)
- [ ] Performance baseline established (measure current replay time)
- [ ] Backup database before migration (optional but recommended)

---

## Implementation Steps

### Step 1: Create ProgressSnapshot Model (60 min)

#### 1.1 Add ProgressSnapshot Model to models.py

Add this AFTER Outbox models, BEFORE relationship definitions:

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

#### 1.2 Create Alembic Migration

```bash
# In backend container
alembic revision --autogenerate -m "Add ProgressSnapshot model for event sourcing optimization"
```

**Review migration file** - verify it includes:
- `progresssnapshot` table creation
- Foreign keys to `userstoryprogress` and `usernodechoice`
- Index on `(progress_id, choice_id)` for fast snapshot lookup
- All columns: id, progress_id, choice_id, story_state, current_node_id, created_at

#### 1.3 Apply Migration

```bash
alembic upgrade head
alembic current  # Verify migration applied
```

---

### Step 2: Add Optimized Replay CRUD Functions (90 min)

#### 2.1 Add to backend/app/crud.py

```python
# ==================== Optimized Replay CRUD (Phase 5) ====================

def replay_state_from_head_optimized(
    *,
    session: Session,
    progress_id: uuid.UUID,
    head_choice_id: uuid.UUID | None
) -> dict[str, Any]:
    """
    Reconstruct story_state by replaying events, using snapshots for optimization.

    This is the FINAL SOURCE OF TRUTH for state in event-sourced model.

    Algorithm:
    1. If head is None, return {} (at story start)
    2. Get ancestor chain (root → head)
    3. Find nearest snapshot in ancestor chain
    4. If snapshot exists, start from snapshot and replay events after it
    5. If no snapshot, replay from root

    Args:
        session: Database session
        progress_id: UserStoryProgress ID
        head_choice_id: Current head position (null = story start)

    Returns:
        Reconstructed state dict

    Performance:
        - Without snapshots: O(n) where n = chain length
        - With snapshots: O(k) where k = choices since last snapshot
        - Target: < 10ms for 100-choice chain with snapshots
    """
    if head_choice_id is None:
        return {}  # At story start

    # Get full ancestor chain
    ancestor_chain = get_choice_ancestor_chain(
        session=session,
        choice_id=head_choice_id
    )

    if not ancestor_chain:
        return {}

    # Find nearest snapshot in ancestor chain
    ancestor_ids = [c.id for c in ancestor_chain]

    snapshot_stmt = (
        select(ProgressSnapshot)
        .where(
            ProgressSnapshot.progress_id == progress_id,
            ProgressSnapshot.choice_id.in_(ancestor_ids)
        )
        .order_by(ProgressSnapshot.created_at.desc())
        .limit(1)
    )

    snapshot = session.exec(snapshot_stmt).first()

    if snapshot:
        # Start from snapshot and replay events after it
        state = snapshot.story_state.copy()

        # Find snapshot position in ancestor chain
        snapshot_idx = next(
            i for i, c in enumerate(ancestor_chain)
            if c.id == snapshot.choice_id
        )

        # Replay events AFTER snapshot
        for choice in ancestor_chain[snapshot_idx + 1:]:
            if choice.state_changes:
                state.update(choice.state_changes)
    else:
        # No snapshot - replay from root
        state = {}
        for choice in ancestor_chain:
            if choice.state_changes:
                state.update(choice.state_changes)

    return state


def create_snapshot_if_needed(
    *,
    session: Session,
    progress: UserStoryProgress,
    snapshot_interval: int = 10
) -> ProgressSnapshot | None:
    """
    Create snapshot if we've reached the snapshot interval.

    Call this after making a choice or moving head.

    Args:
        session: Database session
        progress: UserStoryProgress record (must have head_choice_id set)
        snapshot_interval: Create snapshot every N choices (default: 10)

    Returns:
        Created snapshot, or None if not needed

    Example:
        # After creating choice
        progress.head_choice_id = user_choice.id
        snapshot = crud.create_snapshot_if_needed(
            session=session,
            progress=progress,
            snapshot_interval=10
        )
        if snapshot:
            session.add(snapshot)
    """
    if progress.head_choice_id is None:
        return None  # At story start, no snapshot needed

    # Get chain length
    chain = get_choice_ancestor_chain(
        session=session,
        choice_id=progress.head_choice_id
    )
    chain_length = len(chain)

    # Check if we should create snapshot
    if chain_length % snapshot_interval == 0:
        # Check if snapshot already exists at this position
        existing = session.exec(
            select(ProgressSnapshot).where(
                ProgressSnapshot.progress_id == progress.id,
                ProgressSnapshot.choice_id == progress.head_choice_id
            )
        ).first()

        if existing:
            return None  # Already have snapshot at this position

        # Create snapshot
        snapshot = ProgressSnapshot(
            progress_id=progress.id,
            choice_id=progress.head_choice_id,
            story_state=progress.story_state.copy() if progress.story_state else {},
            current_node_id=progress.current_node_id
        )

        return snapshot

    return None


def get_nearest_snapshot(
    *,
    session: Session,
    progress_id: uuid.UUID,
    head_choice_id: uuid.UUID
) -> ProgressSnapshot | None:
    """
    Get nearest snapshot at or before head position.

    Args:
        session: Database session
        progress_id: UserStoryProgress ID
        head_choice_id: Target head position

    Returns:
        Nearest snapshot, or None if no snapshots exist
    """
    # Get ancestor chain to find all possible snapshot positions
    chain = get_choice_ancestor_chain(
        session=session,
        choice_id=head_choice_id
    )

    if not chain:
        return None

    ancestor_ids = [c.id for c in chain]

    # Find most recent snapshot in ancestor chain
    statement = (
        select(ProgressSnapshot)
        .where(
            ProgressSnapshot.progress_id == progress_id,
            ProgressSnapshot.choice_id.in_(ancestor_ids)
        )
        .order_by(ProgressSnapshot.created_at.desc())
        .limit(1)
    )

    return session.exec(statement).first()
```

---

### Step 3: Update Choice Endpoint to Use Derived State (60 min)

#### 3.1 Modify make_story_choice in backend/app/api/routes/user_story_progress.py

Find the section where `progress.story_state` is updated and replace with derived replay:

**BEFORE (Phase 4):**
```python
    # Update head pointer (atomic move)
    progress.head_choice_id = user_choice.id
    progress.head_version += 1
    progress.current_node_id = choice.to_node_id

    # TRANSITION: Still update story_state mutably for backward compat
    if choice.sets_state:
        if progress.story_state:
            progress.story_state.update(choice.sets_state)
        else:
            progress.story_state = choice.sets_state
```

**AFTER (Phase 5):**
```python
    # Update head pointer (atomic move)
    progress.head_choice_id = user_choice.id
    progress.head_version += 1

    # FINAL: Always derive state from events (single source of truth)
    progress.story_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    progress.current_node_id = crud.get_current_node_from_head(
        session=session,
        head_choice_id=progress.head_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version
    )

    # Create snapshot if needed (every 10 choices)
    snapshot = crud.create_snapshot_if_needed(
        session=session,
        progress=progress,
        snapshot_interval=10
    )
    if snapshot:
        session.add(snapshot)
```

---

### Step 4: Update Undo Endpoint to Use Derived State (30 min)

#### 4.1 Modify undo_story_choice in backend/app/api/routes/user_story_progress.py

Replace mutable state update with derived replay:

**BEFORE (Phase 3):**
```python
    # Move head to parent
    progress.head_choice_id = current_choice.parent_choice_id
    progress.head_version += 1

    # Replay state from new head
    progress.story_state = replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
```

**AFTER (Phase 5):**
```python
    # Move head to parent
    progress.head_choice_id = current_choice.parent_choice_id
    progress.head_version += 1

    # FINAL: Use optimized replay with snapshots
    progress.story_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
```

---

### Step 5: Update Jump Endpoint to Use Derived State (30 min)

#### 5.1 Modify jump_story_head in backend/app/api/routes/user_story_progress.py

Replace mutable state update with derived replay:

**BEFORE (Phase 3):**
```python
    # Move head to target
    progress.head_choice_id = target_choice_id
    progress.head_version += 1

    # Replay state from new head
    progress.story_state = replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
```

**AFTER (Phase 5):**
```python
    # Move head to target
    progress.head_choice_id = target_choice_id
    progress.head_version += 1

    # FINAL: Use optimized replay with snapshots
    progress.story_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
```

---

### Step 6: Add Snapshot Management Endpoints (Optional, 45 min)

#### 6.1 Add Snapshot Routes to backend/app/api/routes/user_story_progress.py

Add these optional admin endpoints for snapshot management:

```python
@router.get("/{story_id}/snapshots", response_model=ProgressSnapshotsPublic)
def read_story_snapshots(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Get all snapshots for this story progress (admin/debug).

    Useful for monitoring snapshot coverage and debugging replay.
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

    # Get all snapshots for this progress
    statement = (
        select(ProgressSnapshot)
        .where(ProgressSnapshot.progress_id == progress.id)
        .order_by(ProgressSnapshot.created_at.asc())
    )

    snapshots = session.exec(statement).all()

    return ProgressSnapshotsPublic(
        data=snapshots,
        count=len(snapshots)
    )


@router.post("/{story_id}/snapshots/create", response_model=ProgressSnapshotPublic)
def create_story_snapshot(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Manually create snapshot at current head position (admin/debug).

    Normally snapshots are created automatically every N choices.
    This endpoint allows manual snapshot creation for testing.
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
        raise HTTPException(
            status_code=400,
            detail="Cannot create snapshot at story start"
        )

    # Check if snapshot already exists
    existing = session.exec(
        select(ProgressSnapshot).where(
            ProgressSnapshot.progress_id == progress.id,
            ProgressSnapshot.choice_id == progress.head_choice_id
        )
    ).first()

    if existing:
        return existing  # Already have snapshot

    # Create snapshot
    snapshot = ProgressSnapshot(
        progress_id=progress.id,
        choice_id=progress.head_choice_id,
        story_state=progress.story_state.copy() if progress.story_state else {},
        current_node_id=progress.current_node_id
    )

    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    return snapshot
```

---

### Step 7: Add Performance Monitoring (60 min)

#### 7.1 Add Replay Performance Metrics

Add logging to measure replay performance:

```python
# At top of crud.py
import time
import logging

logger = logging.getLogger(__name__)


# In replay_state_from_head_optimized function
def replay_state_from_head_optimized(
    *,
    session: Session,
    progress_id: uuid.UUID,
    head_choice_id: uuid.UUID | None
) -> dict[str, Any]:
    """..."""
    start_time = time.perf_counter()

    # ... existing replay logic ...

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Log performance
    chain_length = len(ancestor_chain) if ancestor_chain else 0
    used_snapshot = snapshot is not None

    logger.info(
        f"Replay: {elapsed_ms:.2f}ms | "
        f"chain_length={chain_length} | "
        f"used_snapshot={used_snapshot}"
    )

    # Warn if replay is slow
    if elapsed_ms > 50:
        logger.warning(
            f"Slow replay detected: {elapsed_ms:.2f}ms for {chain_length} choices"
        )

    return state
```

#### 7.2 Add Snapshot Coverage Metrics

```python
def get_snapshot_coverage(
    *, session: Session, progress_id: uuid.UUID
) -> dict[str, Any]:
    """
    Get snapshot coverage metrics for monitoring.

    Args:
        session: Database session
        progress_id: UserStoryProgress ID

    Returns:
        Dict with coverage metrics

    Example:
        {
            "total_choices": 47,
            "total_snapshots": 4,
            "coverage_percent": 85.1,
            "max_gap": 12,
            "avg_gap": 10.5
        }
    """
    # Get total choices
    total_choices = session.exec(
        select(func.count(UserNodeChoice.id)).where(
            UserNodeChoice.progress_id == progress_id
        )
    ).one()

    # Get snapshot count
    snapshot_count = session.exec(
        select(func.count(ProgressSnapshot.id)).where(
            ProgressSnapshot.progress_id == progress_id
        )
    ).one()

    # Calculate coverage
    if total_choices == 0:
        return {
            "total_choices": 0,
            "total_snapshots": 0,
            "coverage_percent": 0,
            "max_gap": 0,
            "avg_gap": 0
        }

    # Get snapshots
    snapshots = session.exec(
        select(ProgressSnapshot)
        .where(ProgressSnapshot.progress_id == progress_id)
        .order_by(ProgressSnapshot.created_at.asc())
    ).all()

    # Calculate gaps between snapshots
    gaps = []
    if snapshots:
        for i in range(len(snapshots)):
            # Get chain length at this snapshot
            chain = get_choice_ancestor_chain(
                session=session,
                choice_id=snapshots[i].choice_id
            )

            if i == 0:
                gap = len(chain)  # Gap from root to first snapshot
            else:
                prev_chain = get_choice_ancestor_chain(
                    session=session,
                    choice_id=snapshots[i-1].choice_id
                )
                gap = len(chain) - len(prev_chain)

            gaps.append(gap)

    max_gap = max(gaps) if gaps else 0
    avg_gap = sum(gaps) / len(gaps) if gaps else 0
    coverage_percent = (snapshot_count / (total_choices / 10)) * 100 if total_choices > 0 else 0

    return {
        "total_choices": total_choices,
        "total_snapshots": snapshot_count,
        "coverage_percent": min(coverage_percent, 100),
        "max_gap": max_gap,
        "avg_gap": round(avg_gap, 1)
    }
```

---

### Step 8: Testing (120 min)

#### 8.1 Create backend/app/tests/test_event_sourcing.py

```python
"""Tests for full event sourcing implementation (Phase 5)."""

import uuid
import time
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import ProgressSnapshot, UserNodeChoice
from app import crud


def test_snapshot_created_every_10_choices(
    client: TestClient, session: Session, user_persona_with_story
):
    """Test that snapshots are created automatically every 10 choices."""
    user_persona_id, story_id = user_persona_with_story

    # Make 25 choices
    for i in range(25):
        response = client.get(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node"
        )
        current_node = response.json()

        if not current_node["choices"]:
            break  # End node reached

        choice_id = current_node["choices"][0]["id"]
        response = client.post(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}"
        )
        assert response.status_code == 200

    # Get progress
    progress = crud.get_user_story_progress(
        session=session,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Check snapshots
    snapshots = session.exec(
        select(ProgressSnapshot).where(
            ProgressSnapshot.progress_id == progress.id
        )
    ).all()

    # Should have snapshots at choices 10, 20 (assuming we made at least 20 choices)
    assert len(snapshots) >= 2

    # Verify snapshot positions
    for snapshot in snapshots:
        chain = crud.get_choice_ancestor_chain(
            session=session,
            choice_id=snapshot.choice_id
        )
        chain_length = len(chain)

        # Chain length should be multiple of 10
        assert chain_length % 10 == 0


def test_replay_uses_snapshots(
    client: TestClient, session: Session, user_persona_with_story
):
    """Test that replay uses snapshots when available."""
    user_persona_id, story_id = user_persona_with_story

    # Make 15 choices to trigger snapshot at choice 10
    for i in range(15):
        response = client.get(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node"
        )
        current_node = response.json()

        if not current_node["choices"]:
            break

        choice_id = current_node["choices"][0]["id"]
        client.post(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}"
        )

    # Get progress
    progress = crud.get_user_story_progress(
        session=session,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Verify snapshot exists
    snapshot = crud.get_nearest_snapshot(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
    assert snapshot is not None

    # Replay with snapshot
    replayed_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Should match current state
    assert replayed_state == progress.story_state


def test_replay_performance_with_snapshots(
    client: TestClient, session: Session, user_persona_with_story
):
    """Test that replay with snapshots is faster than without."""
    user_persona_id, story_id = user_persona_with_story

    # Make 50 choices (will create snapshots at 10, 20, 30, 40, 50)
    for i in range(50):
        response = client.get(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node"
        )
        current_node = response.json()

        if not current_node["choices"]:
            break

        choice_id = current_node["choices"][0]["id"]
        client.post(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}"
        )

    # Get progress
    progress = crud.get_user_story_progress(
        session=session,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Measure replay WITH snapshots
    start = time.perf_counter()
    state_with_snapshot = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
    time_with_snapshot = (time.perf_counter() - start) * 1000

    # Measure replay WITHOUT snapshots (from root)
    start = time.perf_counter()
    state_without_snapshot = crud.replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
    time_without_snapshot = (time.perf_counter() - start) * 1000

    # Both should produce same result
    assert state_with_snapshot == state_without_snapshot

    # With snapshot should be faster (or at least not slower)
    # Target: < 10ms with snapshots
    assert time_with_snapshot < 10, f"Replay too slow: {time_with_snapshot}ms"

    print(f"Replay performance:")
    print(f"  With snapshots: {time_with_snapshot:.2f}ms")
    print(f"  Without snapshots: {time_without_snapshot:.2f}ms")
    print(f"  Speedup: {time_without_snapshot / time_with_snapshot:.2f}x")


def test_state_always_derived_from_events(
    client: TestClient, session: Session, user_persona_with_story
):
    """Test that story_state is ALWAYS derived from events, never mutated."""
    user_persona_id, story_id = user_persona_with_story

    # Make choice
    response = client.get(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node"
    )
    current_node = response.json()
    choice_id = current_node["choices"][0]["id"]

    response = client.post(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}"
    )
    assert response.status_code == 200
    progress_data = response.json()

    # Get progress from database
    progress = crud.get_user_story_progress(
        session=session,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Replay state from events
    replayed_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Stored state MUST match replayed state
    assert progress.story_state == replayed_state

    # API response state MUST match replayed state
    assert progress_data["story_state"] == replayed_state


def test_undo_derives_state_from_events(
    client: TestClient, session: Session, user_persona_with_progress
):
    """Test that undo derives state from events (not mutable update)."""
    user_persona_id, story_id = user_persona_with_progress

    # Undo
    response = client.post(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/undo"
    )
    assert response.status_code == 200

    # Get progress
    progress = crud.get_user_story_progress(
        session=session,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Replay state
    replayed_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Must match
    assert progress.story_state == replayed_state


def test_jump_derives_state_from_events(
    client: TestClient, session: Session, user_persona_with_progress
):
    """Test that jump derives state from events (not mutable update)."""
    user_persona_id, story_id = user_persona_with_progress

    # Get timeline
    response = client.get(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/timeline"
    )
    timeline = response.json()

    # Jump to start
    response = client.post(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/jump",
        json={
            "choice_id": None,
            "expected_head_version": timeline["head_version"]
        }
    )
    assert response.status_code == 200

    # Get progress
    progress = crud.get_user_story_progress(
        session=session,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Replay state
    replayed_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Must match (should be empty dict since at start)
    assert progress.story_state == replayed_state
    assert replayed_state == {}


def test_snapshot_coverage_metrics(
    client: TestClient, session: Session, user_persona_with_story
):
    """Test snapshot coverage metrics calculation."""
    user_persona_id, story_id = user_persona_with_story

    # Make 35 choices
    for i in range(35):
        response = client.get(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node"
        )
        current_node = response.json()

        if not current_node["choices"]:
            break

        choice_id = current_node["choices"][0]["id"]
        client.post(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}"
        )

    # Get progress
    progress = crud.get_user_story_progress(
        session=session,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Get coverage metrics
    metrics = crud.get_snapshot_coverage(
        session=session,
        progress_id=progress.id
    )

    # Verify metrics
    assert metrics["total_choices"] >= 30
    assert metrics["total_snapshots"] >= 3  # At 10, 20, 30
    assert metrics["coverage_percent"] > 0
    assert metrics["max_gap"] <= 10  # Should never exceed interval
    assert metrics["avg_gap"] <= 10
```

#### 8.2 Run Tests

```bash
# In backend container
pytest app/tests/test_event_sourcing.py -v

# Expected output:
# test_snapshot_created_every_10_choices PASSED
# test_replay_uses_snapshots PASSED
# test_replay_performance_with_snapshots PASSED
# test_state_always_derived_from_events PASSED
# test_undo_derives_state_from_events PASSED
# test_jump_derives_state_from_events PASSED
# test_snapshot_coverage_metrics PASSED
```

---

## Verification Checklist

After completing all steps, verify:

- [ ] ProgressSnapshot model created and migrated
- [ ] Optimized replay functions implemented
- [ ] Choice endpoint uses derived state (no mutable updates)
- [ ] Undo endpoint uses derived state
- [ ] Jump endpoint uses derived state
- [ ] Snapshots created automatically every 10 choices
- [ ] Replay uses snapshots when available
- [ ] Replay performance < 10ms with snapshots
- [ ] All state derived from events (events are source of truth)
- [ ] All tests pass (7 tests)
- [ ] No mutable state updates remaining

---

## Manual Testing

### Test Snapshot Creation

```bash
# Make 25 choices
for i in {1..25}; do
  curl -X POST "http://localhost:8000/api/v1/user-personas/{id}/stories/{id}/choices/{id}" \
    -H "Authorization: Bearer {token}"
done

# Check snapshots
docker compose exec backend bash
psql $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT COUNT(*) FROM progresssnapshot WHERE progress_id = 'YOUR_PROGRESS_ID';"

# Should return 2 (at choices 10 and 20)
```

### Test Replay Performance

```bash
# In backend logs, look for replay timing
docker compose logs backend | grep "Replay:"

# Example output:
# Replay: 3.45ms | chain_length=15 | used_snapshot=True
# Replay: 8.21ms | chain_length=47 | used_snapshot=True
# Replay: 1.23ms | chain_length=5 | used_snapshot=False
```

### Test State Consistency

```bash
# Make choice, then verify state matches replay
curl -X POST ".../choices/{id}" | jq '.story_state' > actual.json

# Get replayed state (via internal API or debug endpoint)
# Compare files - should be identical
diff actual.json replayed.json
# (empty output = identical)
```

---

## Troubleshooting

### Problem: Snapshots not being created

**Solution:**
```bash
# Check snapshot creation logic
docker compose exec backend bash
python3 <<EOF
from app.core.db import engine
from app import crud
from sqlmodel import Session

with Session(engine) as session:
    progress = session.get(UserStoryProgress, "YOUR_PROGRESS_ID")
    snapshot = crud.create_snapshot_if_needed(
        session=session,
        progress=progress,
        snapshot_interval=10
    )
    if snapshot:
        print(f"Created snapshot: {snapshot.id}")
    else:
        print("No snapshot needed")
EOF
```

### Problem: Replay is slow (> 10ms)

**Solution:**
- Check if snapshots exist: `SELECT COUNT(*) FROM progresssnapshot WHERE progress_id = 'X'`
- Verify snapshot interval is reasonable (10 is good default)
- Check chain length: Long chains without snapshots will be slow
- Consider reducing snapshot_interval to 5 for very active stories

### Problem: Replayed state doesn't match stored state

**Solution:**
```bash
# This indicates a bug - replay is source of truth
# Check for mutable state updates that weren't removed
grep -r "story_state.update" backend/app/api/routes/

# Should return NO results (all mutable updates removed)

# Check state_changes in events
docker compose exec backend bash
psql $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT id, state_changes FROM usernodechoice WHERE progress_id = 'X' ORDER BY choice_time;"
```

### Problem: Snapshots consuming too much storage

**Solution:**
```bash
# Check snapshot size
psql $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT pg_size_pretty(pg_total_relation_size('progresssnapshot'));"

# If too large, increase snapshot_interval
# Or implement snapshot pruning (keep only last N snapshots)

# Prune old snapshots (keep last 5)
DELETE FROM progresssnapshot
WHERE id NOT IN (
  SELECT id FROM progresssnapshot
  WHERE progress_id = 'X'
  ORDER BY created_at DESC
  LIMIT 5
);
```

---

## Quick Command Reference

```bash
# Check snapshot count
psql $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT progress_id, COUNT(*) as snapshot_count FROM progresssnapshot GROUP BY progress_id;"

# Check snapshot coverage
psql $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT
    p.id,
    COUNT(DISTINCT c.id) as total_choices,
    COUNT(DISTINCT s.id) as total_snapshots,
    ROUND(100.0 * COUNT(DISTINCT s.id) / NULLIF(COUNT(DISTINCT c.id) / 10, 0), 1) as coverage_percent
  FROM userstoryprogress p
  LEFT JOIN usernodechoice c ON c.progress_id = p.id
  LEFT JOIN progresssnapshot s ON s.progress_id = p.id
  GROUP BY p.id;"

# Monitor replay performance
docker compose logs -f backend | grep "Replay:"

# Check for slow replays
docker compose logs backend | grep "Slow replay"

# Verify no mutable state updates
grep -r "story_state.update\|story_state\[" backend/app/api/routes/
# (should return nothing)
```

---

## Time Breakdown

| Step | Task | Time |
|------|------|------|
| 1 | Create ProgressSnapshot model | 60 min |
| 2 | Add optimized replay CRUD functions | 90 min |
| 3 | Update choice endpoint | 60 min |
| 4 | Update undo endpoint | 30 min |
| 5 | Update jump endpoint | 30 min |
| 6 | Add snapshot management endpoints | 45 min |
| 7 | Add performance monitoring | 60 min |
| 8 | Testing | 120 min |
| **Total** | | **~12 hours** |

---

## Success Criteria

✅ **Phase 5 Complete When:**
1. ProgressSnapshot model exists and migrated
2. Replay functions use snapshots for optimization
3. All endpoints (choice/undo/jump) derive state from events
4. NO mutable state updates remain in codebase
5. Snapshots created automatically every 10 choices
6. Replay performance < 10ms for 100-choice chain with snapshots
7. Replayed state ALWAYS matches stored state
8. Events are single source of truth
9. All tests pass (7 tests minimum)
10. Performance monitoring shows replay < 50ms without snapshots
11. No errors in backend logs
12. State consistency validated across all operations

---

## Next Steps

After Phase 5 is complete:
1. **Monitor production metrics** - track replay times, snapshot coverage
2. **Tune snapshot interval** - adjust based on actual usage patterns
3. **Implement snapshot pruning** - keep only last N snapshots per progress
4. **Add snapshot compression** - compress old snapshots to save space
5. **Consider projection tables** - if replay still too slow, add dedicated projection tables
6. **Celebrate!** 🎉 Full event sourcing migration complete!

---

## Migration Complete!

Congratulations! You've successfully migrated from mutable state to full event sourcing:

✅ Phase 1: Event tree structure
✅ Phase 2: Replay & projection logic
✅ Phase 3: Undo & rewind APIs
✅ Phase 4: Real-time distribution
✅ Phase 5: Full event sourcing

**Your CYOA system now has:**
- Immutable event stream as source of truth
- Branching timelines with undo/rewind
- Real-time updates via WebSocket
- Optimized replay with snapshotting
- Deterministic state reconstruction

---

**Questions? See:**
- CYOA_MIGRATION_PLAN.md - Overall strategy
- CYOA_MIGRATION_ADDENDUM.md - TinyFoot patterns
- backend/docs/RULES.md - Backend conventions
- STORY_SYSTEM.md - Original system documentation
