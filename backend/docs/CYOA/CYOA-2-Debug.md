# Phase 2 DEBUG of replay and projection logic

**Goal of Debug Session:**  determine errors in control flow, design, call hierarchy, or implementation.

**Intent of CYOA Phase 2 Work:** Add ability to reconstruct `story_state` from event chain (root → head)

**Status: ✅ FULLY RESOLVED** (2026-01-04)

**Test Results: 15/15 PASSING (100%)** ✅
- ✅ Phase 1: Story & Node Management (4/4 tests)
- ✅ Phase 2: Progress & Choice Making (5/5 tests)
- ✅ Phase 3: Timeline Navigation (3/3 tests)
- ✅ Validation: Event Sourcing (3/3 tests)

**What Was Fixed:**
1. ✅ Test persona creation API contract mismatch (Persona vs UserPersona)
2. ✅ Boolean query issue in SQLAlchemy (`is True` → `== True`)
3. ✅ Trailing comma in validate-state return statement (tuple vs dict)
4. ✅ All CRUD functions verified implemented and in use
5. ✅ All required endpoints verified implemented

**Reference Materials Created:**
- ✅ Debug script: `backend/app/test_scripts/debug_validate_state.py`
- ✅ Test reference card: `backend/app/tests/CYOA_TEST_REFERENCE.md`

**CYOA Implementation Status:**
- CYOA_PHASE2_QUICKREF.md ✅ Completed
- CYOA_PHASE3 (Timeline Navigation) ✅ Implemented
- CYOA_PHASE5 (Real-time events) ⚠️ Partially implemented
- Frontend work: ⏸️ Blocked on Test 15 resolution

---

## Pre-Debug Checklist
- [X] Branch with all changes built
- [X] Branch deployed to dockerized staging environment
- [X] All services running, other test_scripts (non story) passing
- [X] Auth helper passing.

## Step 1: Review CRUD Functions

### Location: `backend/app/crud.py`

#### ✅ ALL FUNCTIONS IMPLEMENTED AND IN USE

#### 1.1 ✅ get_choice_ancestor_chain (line 1704)
- **Purpose**: Traverse parent pointers from choice → root
- **Returns**: `list[UserNodeChoice]` in root → target order
- **Used by**:
  - `replay_state_from_head` (line 1760)
  - `validate_ancestor_constraint` (line 1882)
  - `read_story_timeline` endpoint (routes line 772)
- **Status**: ✅ Fully implemented

#### 1.2 ✅ replay_state_from_head (line 1736)
- **Purpose**: Reconstruct state by replaying events root → head
- **Returns**: `dict[str, Any]` (reconstructed state)
- **Used by**:
  - `move_head_to_choice` (line 1761 in this file)
  - `make_story_choice` endpoint (routes line 335) - for validation
  - `validate_story_state` endpoint (routes line 457) - diagnostics
- **Status**: ✅ Fully implemented

#### 1.3 ✅ get_current_node_from_head (line 1777)
- **Purpose**: Derive current_node_id from head position
- **Returns**: `uuid.UUID` of current node
- **Used by**:
  - `move_head_to_choice` (line 1793 in this file)
- **Status**: ✅ Fully implemented

#### 1.4 ✅ get_choice_children (line 1822)
- **Purpose**: Get direct children of a choice (admin/debug)
- **Returns**: `list[UserNodeChoice]`
- **Used by**: Admin tools (not in core gameplay flow)
- **Status**: ✅ Fully implemented

#### 1.5 ✅ validate_ancestor_constraint (line 1851)
- **Purpose**: Verify target is ancestor of current head
- **Returns**: `bool`
- **Used by**:
  - `jump_story_head` endpoint (routes line 654) - prevents forward jumps
- **Status**: ✅ Fully implemented

#### 1.6 ✅ move_head_to_choice (line 1887)
- **Purpose**: Core undo/jump logic - move head + replay state
- **Returns**: `UserStoryProgress` (mutated)
- **Used by**:
  - `undo_story_choice` endpoint (routes line 548)
  - `jump_story_head` endpoint (routes line 671)
- **Side effects**:
  - Updates `head_choice_id`
  - Increments `head_version`
  - Replays `story_state` from new head
  - Derives `current_node_id`
  - Resets `is_completed`
- **Status**: ✅ Fully implemented

## Step 2: review validation endpoint

### Location: `backend/app/api/routes/user_story_progress.py`

#### ✅ COMPLETE: Endpoints Required by Design (All Implemented)

**Phase 1-2: Story Creation & Progress**
1. `POST /{story_id}` → `create_user_story_progress` (line 115)
   - Creates new progress, locks to current_version
   - Uses: Story start node query

2. `GET /{story_id}` → `read_user_story_progress` (line 86)
   - Returns progress with current state

3. `GET /{story_id}/current-node` → `get_current_node` (line 188)
   - Returns current node + available choices
   - Uses: `crud.get_available_choices`

**Phase 2: Choice Making with Replay Validation**
4. `POST /{story_id}/choices/{choice_id}` → `make_story_choice` (line 227)
   - ✅ Creates UserNodeChoice with parent_choice_id
   - ✅ Updates head_choice_id and head_version
   - ✅ Mutable update to story_state (line 328-333)
   - ✅ Calls `replay_state_from_head` for validation (line 335)
   - ✅ Logs warning on mismatch (line 342-348)

**Phase 3: Timeline Navigation**
5. `POST /{story_id}/undo` → `undo_story_choice` (line 488)
   - ✅ Uses `crud.move_head_to_choice` (line 548)
   - ✅ Publishes HeadMoved event to Redis

6. `POST /{story_id}/jump` → `jump_story_head` (line 579)
   - ✅ Uses `crud.validate_ancestor_constraint` (line 654)
   - ✅ Uses `crud.move_head_to_choice` (line 671)
   - ✅ Optimistic concurrency check (line 633)
   - ✅ Publishes HeadMoved event to Redis

7. `GET /{story_id}/timeline` → `read_story_timeline` (line 702)
   - ✅ Uses `crud.get_choice_ancestor_chain` (line 772)
   - Returns breadcrumb trail (root → head)

**Phase 2 Diagnostics**
8. `GET /{story_id}/validate-state` → `validate_story_state` (line 419)
   - ✅ Uses `crud.replay_state_from_head` (line 457)
   - Compares stored vs replayed state
   - Returns match status + differences

## Step 3: review update endpoint - make_story_choice

### Location: `backend/app/api/routes/user_story_progress.py` (line 227)

#### ✅ CONFIRMED: make_story_choice keeps BOTH mutable updates AND replay validation

**Implementation Details:**

1. **Creates UserNodeChoice** (line 310-320)
   - Sets `parent_choice_id` = current `head_choice_id` ✅
   - Stores `state_changes` from NodeChoice.sets_state ✅
   - Flush to get ID ✅

2. **Updates Head Pointer** (line 322-325)
   - Sets `head_choice_id` = new UserNodeChoice.id ✅
   - Increments `head_version` ✅
   - Sets `current_node_id` ✅

3. **Mutable State Update** (line 328-333)
   - Updates `progress.story_state` via dict merge ✅
   - Phase 2 pattern: denormalized cache

4. **Replay Validation** (line 335-348)
   - Calls `crud.replay_state_from_head` ✅
   - Compares replayed vs stored ✅
   - Logs warning on mismatch ✅

**Design Compliance:** ✅ CORRECT
- Phase 2: Mutable updates PRIMARY, replay VALIDATION
- Phase 5: Replay becomes PRIMARY (not yet implemented)

---

## Step 4: Investigate Test 15 Failure (validate-state endpoint)

### Current Status
- **Endpoint**: `GET /user-personas/{id}/stories/{story_id}/validate-state`
- **Error**: 500 Internal Server Error
- **Test**: #15 - State Replay Correctness

### Debug Tools
Run the debug script to investigate:
```bash
cd backend/app/test_scripts
python3 debug_validate_state.py
```

### Potential Causes
1. **Null head_choice_id**: After Test 11 (jump to start), head_choice_id is None
   - `replay_state_from_head` should handle None (line 1756-1757 in crud.py)
   - Returns empty dict `{}` when head_choice_id is None
   - This should match stored state if also at start

2. **Missing UserNodeChoice record**: Database integrity issue
   - `get_choice_ancestor_chain` will raise ValueError if choice not found (line 1718)
   - Check: Are all UserNodeChoice records present?

3. **Wrong progress_id validation**: Mismatch in ownership
   - Line 1764 validates all choices belong to progress_id
   - Check: Do choices have correct progress_id?

4. **State mismatch after undo/jump**: Replay logic bug
   - After timeline navigation, replayed state should match stored
   - Check: Is `move_head_to_choice` correctly updating story_state?

### Expected Behavior
After test sequence:
1. Make choice → state = `{"path_taken": "left"}`
2. Undo → state = `{}`
3. Jump to start → state = `{}`
4. validate-state → Should return `{"match": true}`

### Investigation Steps
1. Run `debug_validate_state.py` to see actual error
2. Check backend logs for stack trace
3. Verify head_choice_id value in progress
4. Manually test replay_state_from_head with test data

---

## Debug Notes:
Phase 2 CYOA State Replay Functions begin at line 1689 `backend/app/crud.py`

# ==================== Phase 2 CYOA: State Replay Functions ====================
#
# These functions implement event sourcing replay logic:
#
# 1. get_choice_ancestor_chain() - Traverses parent pointers from head to root
# 2. replay_state_from_head() - Reconstructs state by merging state_changes
# 3. get_current_node_from_head() - Derives current node from head position
#
# In Phase 2, these functions VALIDATE existing mutable state.
# In Phase 5, these become the SOURCE OF TRUTH for state.
#
# Performance: O(n) where n = chain length. Target < 50ms for 100 choices.
# Optimization: Snapshots added in Phase 5 reduce replay cost.
# ===========================================================================


`get_choice_ancestor_chain`:
begins at 1704, returns `list[UserNodeChoice]`

1:  get_choice_ancestor_chain is called by replay_state_from_head 
(replay state_from_head begins line 1736 in crud.py, call is at line 1760)

2:  get_choice_ancestor_chain is called by validate_ancestor_constraint (validate ancestor_constraint begins line 1851, call is at line 1882)


`replay_state_by_head` begins at 1736, returns `dict[string, Any]`

`get_current_node_from_head` begins at 1777, returns UUID

`get_choice_children` returns `list [UserNodeChoice]`, begins at 1822 (admin/debug function)


### This is copied out from crud.py for analysis purposes.  changes to either are not synchronized, this is throw away for this session.

```python

def get_choice_ancestor_chain(
    *, session: Session, choice_id: uuid.UUID
) -> list[UserNodeChoice]:
    """
    Get ancestor chain from root to specified choice (inclusive).

    Returns events in order: [root_choice, ..., parent_choice, choice_id]
    Used for replay and timeline display.

    Args:
        session: Database session
        choice_id: Target choice UUID

    Returns:
        List of UserNodeChoice objects from root to target (ordered)

    Raises:
        ValueError: If choice_id doesn't exist in database
    """
    chain = []
    current_id = choice_id

    while current_id is not None:
        choice = session.get(UserNodeChoice, current_id)
        if not choice:
            # If we can't find a choice in the chain, something is corrupt
            raise ValueError(f"Choice {current_id} not found in database (data corruption)")
        chain.append(choice)
        current_id = choice.parent_choice_id

    return list(reversed(chain))  # Root → head order

def replay_state_from_head(
    *, session: Session, progress_id: uuid.UUID, head_choice_id: uuid.UUID | None
) -> dict[str, Any]:
    """
    Reconstruct story_state by replaying all events from root to head.

    This is the SOURCE OF TRUTH for state in event-sourced model.
    The UserStoryProgress.story_state field becomes a denormalized cache.

    Args:
        session: Database session
        progress_id: UserStoryProgress UUID (for validation)
        head_choice_id: Current head position (null = story start)

    Returns:
        Reconstructed state dictionary

    Raises:
        ValueError: If choice doesn't belong to progress_id
    """
    if head_choice_id is None:
        return {}  # At story start

    # Get all events from root to head
    chain = get_choice_ancestor_chain(session=session, choice_id=head_choice_id)

    # Validate all choices belong to this progress
    for choice in chain:
        if choice.progress_id != progress_id:
            raise ValueError(
                f"Choice {choice.id} doesn't belong to progress {progress_id}"
            )

    # Replay events (shallow merge)
    state: dict[str, Any] = {}
    for choice in chain:
        if choice.state_changes:
            state.update(choice.state_changes)

    return state

def get_current_node_from_head(
    *,
    session: Session,
    head_choice_id: uuid.UUID | None,
    story_id: uuid.UUID,
    story_version: int,
) -> uuid.UUID:
    """
    Derive current_node_id from head position.

    If head_choice_id is None, return start node.
    Otherwise, return to_node_id of head choice.

    Args:
        session: Database session
        head_choice_id: Current head position (null = story start)
        story_id: Story UUID (for finding start node)
        story_version: Story version (for finding start node)

    Returns:
        UUID of current story node

    Raises:
        ValueError: If no start node found or head choice missing
    """
    if head_choice_id is None:
        # At story start - find start node
        statement = select(StoryNode).where(
            StoryNode.story_id == story_id,
            StoryNode.story_version == story_version,
            StoryNode.is_start_node == True,  # noqa: E712
        )
        start_node = session.exec(statement).first()
        if not start_node:
            raise ValueError(
                f"No start node for story {story_id} version {story_version}"
            )
        return start_node.id

    # Return destination of head choice
    choice = session.get(UserNodeChoice, head_choice_id)
    if not choice:
        raise ValueError(f"Head choice {head_choice_id} not found")
    return choice.to_node_id

def get_choice_children(
    *, session: Session, choice_id: uuid.UUID
) -> list[UserNodeChoice]:
    """
    Get all direct children of a choice (for debugging/admin tools).

    In normal gameplay, children are hidden (abandoned branches).
    This is used for admin visualization of the full event tree.

    Args:
        session: Database session
        choice_id: Parent choice UUID

    Returns:
        List of child UserNodeChoice objects
    """
    statement = select(UserNodeChoice).where(
        UserNodeChoice.parent_choice_id == choice_id
    )
    return list(session.exec(statement).all())

# ==================== Phase 3: Timeline Navigation Functions ====================
#
# IMPROVEMENT OVER MIGRATION PLAN:
# The migration plan shows inline replay logic in undo/jump endpoints.
# These helper functions extract common logic for DRY and maintainability.
# This follows TinyFoot functional patterns from RULES.md.
# ==============================================================================

def validate_ancestor_constraint(
    *, session: Session, target_choice_id: uuid.UUID, current_head_id: uuid.UUID
) -> bool:
    """
    Validate that target choice is an ancestor of current head.

    Used by jump endpoint to prevent forward jumps (which would expose hidden branches).
    Forward jumps are prohibited because they would reveal abandoned timeline branches.

    Args:
        session: Database session
        target_choice_id: Proposed jump target
        current_head_id: Current head position

    Returns:
        True if target is ancestor of current head, False otherwise

    Raises:
        ValueError: If current_head_id doesn't exist (via get_choice_ancestor_chain)

    Example:
        # Before jump, validate target is in ancestor chain
        is_ancestor = crud.validate_ancestor_constraint(
            session=session,
            target_choice_id=target,
            current_head_id=progress.head_choice_id
        )
        if not is_ancestor:
            raise HTTPException(400, "Target is not an ancestor")
    """
    # Get ancestor chain from current head to root
    ancestors = get_choice_ancestor_chain(session=session, choice_id=current_head_id)
    ancestor_ids = {c.id for c in ancestors}

    # Check if target is in the ancestor chain
    return target_choice_id in ancestor_ids


def move_head_to_choice(
    *,
    session: Session,
    progress: UserStoryProgress,
    target_choice_id: uuid.UUID | None,
) -> UserStoryProgress:
    """
    Move head pointer to target choice and update derived state.

    This is the core function for undo/jump operations.
    Encapsulates head movement, state replay, and node derivation.

    IMPORTANT: This function uses replay to UPDATE story_state.
    Unlike make_story_choice (which still uses mutable updates in Phase 3),
    timeline navigation MUST replay because we're moving backward in time.

    Args:
        session: Database session
        progress: UserStoryProgress instance to update
        target_choice_id: Target choice (null = story start)

    Returns:
        Updated UserStoryProgress instance (mutated in place)

    Side effects:
        - Updates progress.head_choice_id to target
        - Increments progress.head_version (optimistic lock)
        - Replays state from new head (replaces progress.story_state)
        - Updates progress.current_node_id
        - Resets progress.is_completed flag (might not be at end anymore)

    Raises:
        ValueError: If target_choice_id doesn't exist or state replay fails

    Example:
        # In undo endpoint
        current_choice = session.get(UserNodeChoice, progress.head_choice_id)
        progress = crud.move_head_to_choice(
            session=session,
            progress=progress,
            target_choice_id=current_choice.parent_choice_id  # Move to parent
        )
        session.add(progress)
        session.commit()
    """
    # Move head pointer
    progress.head_choice_id = target_choice_id
    progress.head_version += 1

    # Replay state from new head position
    # Uses Phase 2 replay_state_from_head (NOT the optimized version from Phase 5)
    progress.story_state = replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=target_choice_id,
    )

    # Derive current node from new head position
    progress.current_node_id = get_current_node_from_head(
        session=session,
        head_choice_id=target_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version,
    )

    # Reset completion flag (might not be at end node anymore)
    progress.is_completed = False

    return progress
```