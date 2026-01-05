# CYOA Phase 5 Quick Reference Card
## Full Event Sourcing (Derived State + Snapshotting)

**Last Updated:** 2026-01-04
**Status:** 🎯 Implementation Guide
**Prerequisites:** ✅ Phase 1, 2, 3, 4 complete (see EVENT_SYSTEMS_ALIGNMENT.md)
**Estimated Time:** ~6.5-7.25 hours (core implementation + optional snapshot endpoints)

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

- [X] Phase 4 complete and tested (EVENT_SYSTEMS_ALIGNMENT.md)
  - ✅ Real-time publishing via `realtime_publisher.py`
  - ✅ WebSocket story updates implemented
  - ✅ Direct Redis publish pattern (NO Outbox table)
- [X] Replay correctness validated (Phase 2 tests passing)
- [X] Performance baseline established (measure current replay time)
- [X] Backup database before migration (optional but recommended)

**Note on Real-Time Distribution:**
Phase 4 was implemented following the **Room Chat pattern** (direct Redis publish)
as documented in EVENT_SYSTEMS_ALIGNMENT.md. The Outbox pattern mentioned in
early Phase 4 planning was NOT implemented. Both CYOA and Room Chat systems
use direct Redis publish via `realtime_publisher.py` with graceful degradation.

---

## Implementation Steps

### Step 1: Create ProgressSnapshot Model (60 min)

### SEE PHASE5_MODEL_ADDENDUM FOR IMPLEMENTATION OF FOLLOWING STEPS

#### [x] 1.1 Add ProgressSnapshot Model to models.py

#### [x] 1.2 Create Alembic Migration

#### [x] 1.3 Apply Migration

---
### Step 2: Add Optimized Replay CRUD Functions (90 min)

#### [x] 2.1 Add to backend/app/crud.py

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

**BEFORE :**
```python
# no longer in code, already replaced -
# Original code exists in function, commented out as reference
```

**CURRENT(Phase 5 + Real-Time):**
```python
# this has been migrated to user_story_progress.py in make_story_choice
```

**Note:** need to review: might need to import `publish_event_to_redis` from `app.services.realtime_publisher` and add `background_tasks: BackgroundTasks` parameter to route handler.

---

### Step 4: Update Undo Endpoint to Use Derived State (30 min)

#### 4.1 Modify undo_story_choice in backend/app/api/routes/user_story_progress.py

[X] COMPLETE
---

### [X] complete: Step 5: Update Jump Endpoint to Use Derived State (30 min)

#### [X] 5.1 Modify jump_story_head in backend/app/api/routes/user_story_progress.py

Replace mutable state update with derived replay



---

### [x]  Step 6: Add Snapshot Management Endpoints (Optional, 45 min)

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

### Step 7: Performance Monitoring (Future Enhancement)

**Status:** Deferred to observability setup phase

**Rationale:** Direct logging in CRUD functions is not the preferred pattern.
Performance monitoring should be handled at the route/service layer or via
external observability tools (Prometheus, DataDog, OpenTelemetry).

**Recommended Approach (when implementing):**

**Option A: Route-Level Performance Decorator**
```python
# backend/app/api/deps.py
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def monitor_performance(operation: str):
    """Decorator to monitor endpoint performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info(f"{operation}: {elapsed_ms:.2f}ms")
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.error(f"{operation} failed after {elapsed_ms:.2f}ms: {e}")
                raise
        return wrapper
    return decorator

# Usage in routes:
@router.post("/{story_id}/choices/{choice_id}")
@monitor_performance("make_story_choice")
def make_story_choice(...):
    ...
```

**Option B: External Observability (Recommended for Production)**
- Integrate Prometheus metrics for replay timing
- Use OpenTelemetry tracing for distributed performance analysis
- Structured logging with JSON format for log aggregation

**For MVP:** Skip detailed performance monitoring. Rely on:
- Manual testing with various chain lengths (10, 50, 100+ choices)
- Database query logs to identify slow queries
- Simple endpoint response time logging at route level

#### 7.2 Add Snapshot Coverage Metrics (Optional)

**Note:** This is a useful debugging/monitoring utility but not required for core functionality.

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

#### 8.1 refactor backend/app/tests/test_event_sourcing.py based on actual implementation


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
| 3 | Update choice endpoint (+ real-time) | 60 min |
| 4 | Update undo endpoint (+ real-time) | 30 min |
| 5 | Update jump endpoint (+ real-time) | 30 min |
| 6 | Add snapshot management endpoints (optional) | 45 min |
| 7 | Add performance monitoring (deferred) | ~~60 min~~ |
| 8 | Testing | 120 min |
| **Total (Core)** | | **~6.5 hours** |
| **Total (with optional Step 6)** | | **~7.25 hours** |

**Note:** Steps 3-5 now include real-time event publishing (Phase 4 integration).
Performance monitoring (Step 7) deferred to observability setup phase.

---

## Success Criteria

✅ **Phase 5 Complete When:**
1. ProgressSnapshot model exists and migrated
2. Replay functions use snapshots for optimization (`replay_state_from_head_optimized`)
3. All endpoints (choice/undo/jump) derive state from events (NO mutable updates)
4. All endpoints publish real-time events via `realtime_publisher.py` (Phase 4 integration)
5. NO mutable state updates remain in codebase (`story_state` is always derived)
6. Snapshots created automatically every 10 choices
7. Replay performance < 10ms for 100-choice chain with snapshots
8. Replayed state ALWAYS matches stored state (validation test passes)
9. Events are single source of truth (can delete `story_state` and replay from events)
10. All tests pass (Phase 2, 3, 5 event sourcing tests)
11. Manual testing: Story playthrough with 50+ choices completes successfully
12. WebSocket clients receive real-time updates for choice/undo/jump operations
13. No errors in backend logs
14. State consistency validated across all operations

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
- EVENT_SYSTEMS_ALIGNMENT.md - Real-time event distribution (Phase 4)
- STORY_SYSTEM_V2.md - Current system documentation (Phases 1-4)
- app/services/realtime_publisher.py - Shared Redis publisher implementation
- CYOA_MIGRATION_PLAN.md - Overall strategy
- CYOA_MIGRATION_ADDENDUM.md - TinyFoot patterns
- backend/docs/RULES.md - Backend conventions
