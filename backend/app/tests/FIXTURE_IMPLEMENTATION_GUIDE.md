# Fixture Implementation Guide: Event Sourcing & Branching Tests

**Status**: All tests passing except `test_event_sourcing.py`
**Goal**: Implement fixtures to support snapshot testing and branching story tests
**Date**: 2026-01-05

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Required Fixtures](#required-fixtures)
3. [Implementation Specifications](#implementation-specifications)
4. [Migration Guide](#migration-guide)
5. [Testing Strategy](#testing-strategy)

---

## Current State Analysis

### Existing Fixtures (from conftest.py)

#### ✅ `db_story_with_progress` (lines 403-586)
**Structure**: Linear path with 4 choices
```
Start → Node2 → Node3 → Node4 → Node5 (end)
  ↓       ↓       ↓       ↓
choice1 choice2 choice3 choice4
```

**Returns**: `tuple[Story, UserStoryProgress]`
**Used by**: `test_petri_timeline.py`, `test_story_timeline.py`, `test_user_story_tree.py` (all passing)
**Limitations**:
- Only 4 choices available (insufficient for snapshot tests requiring 25-50 choices)
- No branching (each node has exactly 1 outgoing choice)

---

## Required Fixtures

### Priority 1: Event Sourcing Fixtures

#### 🔴 `db_story_with_long_path` (REQUIRED)
**Purpose**: Support snapshot tests requiring 25-50 choices
**Required by**:
- `test_snapshot_created_every_10_choices` (needs 25 choices)
- `test_replay_performance_with_snapshots` (needs 50 choices)
- `test_snapshot_coverage_metrics` (needs 35 choices)

**Specification**: Linear path with 60 nodes (59 choices)

#### 🔴 `db_story_with_medium_path` (OPTIONAL)
**Purpose**: Support tests requiring 10-20 choices
**Required by**:
- `test_replay_uses_snapshots` (needs 15 choices)

**Specification**: Linear path with 20 nodes (19 choices)
**Note**: Can use `db_story_with_long_path` instead if preferred

---

### Priority 2: Branching Test Fixtures

#### 🟡 `db_story_with_simple_branch` (RECOMMENDED)
**Purpose**: Test basic branching (one branch point, two paths)
**Use cases**:
- Verify multiple `available_choices` at a node
- Test that different choices lead to different nodes
- Test state changes differ by branch taken

**Specification**:
```
Start Node (2 choices)
├─ Choice A → Left Node → Choice L1 → Left End
└─ Choice B → Right Node → Choice R1 → Right End
```
**Total**: 5 nodes, 4 choices (2 from Start, 1 from each branch)

#### 🟡 `db_story_with_deep_branch` (RECOMMENDED)
**Purpose**: Test complex branching with nested branches
**Use cases**:
- Verify state replay on deep paths
- Test timeline navigation in branching stories
- Test undo/jump with multiple branch points

**Specification**:
```
Start (2 choices)
├─ A → Node_A (2 choices)
│   ├─ A1 → Node_A1 → A1_End
│   └─ A2 → Node_A2 → A2_End
└─ B → Node_B (2 choices)
    ├─ B1 → Node_B1 → B1_End
    └─ B2 → Node_B2 → B2_End
```
**Total**: 11 nodes, 10 choices

#### 🟢 `db_story_with_convergent_branch` (OPTIONAL)
**Purpose**: Test branching paths that reconverge
**Use cases**:
- Verify state merging from different paths
- Test that different paths can reach same end

**Specification**:
```
Start (2 choices)
├─ Left → Left_Mid ──┐
└─ Right → Right_Mid ─┴→ Convergence → End
```
**Total**: 6 nodes, 5 choices

---

## Implementation Specifications

### Fixture 1: `db_story_with_long_path`

**Location**: `backend/app/tests/conftest.py`
**Insert after**: `db_story_with_progress` (after line 586)

```python
@pytest.fixture(scope="function")
def db_story_with_long_path(db: Session) -> tuple[Story, UserStoryProgress]:
    """
    Create a story with 60 nodes (59 choices) for testing snapshots.

    This fixture supports event sourcing tests that need to make 25-50 choices
    to test snapshot creation at 10-choice intervals.

    Structure: Linear path Start → N1 → N2 → ... → N59 → End

    Returns:
        tuple[Story, UserStoryProgress]: Story and progress at start (head_version=0)
    """
    # Get or create test user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    if not user:
        from app import crud
        user_in = UserCreate(
            email=settings.EMAIL_TEST_USER,
            password="password",
            is_superuser=False,
        )
        user = crud.create_user(session=db, user_create=user_in)
        db.commit()
        db.refresh(user)

    # Create Persona and UserPersona
    persona = Persona(
        id=uuid4(),
        name="Long Path Test Persona",
        description="For testing long story paths",
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)

    user_persona = UserPersona(
        id=uuid4(),
        user_id=user.id,
        persona_id=persona.id,
        nickname="Long Path Character",
        is_active=True,
    )
    db.add(user_persona)
    db.commit()
    db.refresh(user_persona)

    # Create Story
    story = Story(
        id=uuid4(),
        title="Long Path Test Story",
        description="A story with 60 nodes for testing snapshots",
        owner_id=user.id,
        is_published=True,
        current_version=1,
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    # Create 60 nodes (Start + 58 middle nodes + 1 end node)
    nodes = []

    # Start node
    start_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Start",
        content="Begin the long journey...",
        node_type="text",
        is_start_node=True,
        is_end_node=False,
    )
    db.add(start_node)
    nodes.append(start_node)

    # Create 58 middle nodes
    for i in range(1, 59):
        node = StoryNode(
            id=uuid4(),
            story_id=story.id,
            story_version=1,
            title=f"Node {i}",
            content=f"You continue to step {i}...",
            node_type="text",
            is_start_node=False,
            is_end_node=False,
        )
        db.add(node)
        nodes.append(node)

    # End node
    end_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="End",
        content="You have reached the end of the long path.",
        node_type="text",
        is_start_node=False,
        is_end_node=True,
    )
    db.add(end_node)
    nodes.append(end_node)

    db.commit()
    for node in nodes:
        db.refresh(node)

    # Create 59 choices connecting nodes sequentially
    for i in range(59):
        choice = NodeChoice(
            id=uuid4(),
            from_node_id=nodes[i].id,
            to_node_id=nodes[i + 1].id,
            text=f"Continue to step {i + 1}",
            order=0,
            sets_state={"step": i + 1},  # Track which step we're on
        )
        db.add(choice)

    db.commit()

    # Create UserStoryProgress at start
    progress = UserStoryProgress(
        id=uuid4(),
        user_persona_id=user_persona.id,
        story_id=story.id,
        story_version=1,
        current_node_id=start_node.id,
        is_completed=False,
        story_state={},
        head_choice_id=None,
        head_version=0,
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)

    return (story, progress)
```

**Key Features**:
- 60 nodes total (59 available choices)
- Each choice has unique `sets_state` for tracking
- Numbered nodes for easy debugging
- Follows exact pattern of `db_story_with_progress`

---

### Fixture 2: `db_story_with_simple_branch`

**Location**: `backend/app/tests/conftest.py`
**Insert after**: `db_story_with_long_path`

```python
@pytest.fixture(scope="function")
def db_story_with_simple_branch(db: Session) -> tuple[Story, UserStoryProgress]:
    """
    Create a story with simple branching: one branch point, two paths.

    Structure:
        Start Node (2 choices)
        ├─ "Go Left" → Left Node → "Continue Left" → Left End
        └─ "Go Right" → Right Node → "Continue Right" → Right End

    Use cases:
    - Test that node has multiple available_choices
    - Test that different choices lead to different nodes
    - Test that each branch has different subsequent choices
    - Test that state changes differ by branch

    Returns:
        tuple[Story, UserStoryProgress]: Story and progress at start
    """
    # Get or create test user
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    if not user:
        from app import crud
        user_in = UserCreate(
            email=settings.EMAIL_TEST_USER,
            password="password",
            is_superuser=False,
        )
        user = crud.create_user(session=db, user_create=user_in)
        db.commit()
        db.refresh(user)

    # Create Persona and UserPersona
    persona = Persona(
        id=uuid4(),
        name="Branch Test Persona",
        description="For testing story branching",
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)

    user_persona = UserPersona(
        id=uuid4(),
        user_id=user.id,
        persona_id=persona.id,
        nickname="Branch Test Character",
        is_active=True,
    )
    db.add(user_persona)
    db.commit()
    db.refresh(user_persona)

    # Create Story
    story = Story(
        id=uuid4(),
        title="Simple Branch Test Story",
        description="A story with one branch point",
        owner_id=user.id,
        is_published=True,
        current_version=1,
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    # Create nodes
    start_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Crossroads",
        content="You stand at a crossroads. Which path do you take?",
        node_type="text",
        is_start_node=True,
        is_end_node=False,
    )
    db.add(start_node)

    left_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Left Path",
        content="You walk down the left path through the forest.",
        node_type="text",
        is_start_node=False,
        is_end_node=False,
    )
    db.add(left_node)

    right_node = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Right Path",
        content="You walk down the right path across the bridge.",
        node_type="text",
        is_start_node=False,
        is_end_node=False,
    )
    db.add(right_node)

    left_end = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Forest End",
        content="You emerge from the forest at a cottage.",
        node_type="text",
        is_start_node=False,
        is_end_node=True,
    )
    db.add(left_end)

    right_end = StoryNode(
        id=uuid4(),
        story_id=story.id,
        story_version=1,
        title="Bridge End",
        content="You cross the bridge and reach a castle.",
        node_type="text",
        is_start_node=False,
        is_end_node=True,
    )
    db.add(right_end)

    db.commit()
    db.refresh(start_node)
    db.refresh(left_node)
    db.refresh(right_node)
    db.refresh(left_end)
    db.refresh(right_end)

    # Create choices - NOTE: Start has 2 choices
    choice_left = NodeChoice(
        id=uuid4(),
        from_node_id=start_node.id,
        to_node_id=left_node.id,
        text="Go left through the forest",
        order=0,
        sets_state={"path": "left", "environment": "forest"},
    )
    db.add(choice_left)

    choice_right = NodeChoice(
        id=uuid4(),
        from_node_id=start_node.id,
        to_node_id=right_node.id,
        text="Go right across the bridge",
        order=1,
        sets_state={"path": "right", "environment": "bridge"},
    )
    db.add(choice_right)

    choice_left_continue = NodeChoice(
        id=uuid4(),
        from_node_id=left_node.id,
        to_node_id=left_end.id,
        text="Continue through the forest",
        order=0,
        sets_state={"destination": "cottage"},
    )
    db.add(choice_left_continue)

    choice_right_continue = NodeChoice(
        id=uuid4(),
        from_node_id=right_node.id,
        to_node_id=right_end.id,
        text="Cross the bridge",
        order=0,
        sets_state={"destination": "castle"},
    )
    db.add(choice_right_continue)

    db.commit()

    # Create UserStoryProgress at start
    progress = UserStoryProgress(
        id=uuid4(),
        user_persona_id=user_persona.id,
        story_id=story.id,
        story_version=1,
        current_node_id=start_node.id,
        is_completed=False,
        story_state={},
        head_choice_id=None,
        head_version=0,
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)

    return (story, progress)
```

**Key Features**:
- Start node has 2 choices (critical for branching tests)
- Each branch has distinct state changes
- Each branch leads to different end nodes
- Total of 4 choices (enough for basic testing)

---

### Fixture 3: `db_story_with_deep_branch` (Optional but Recommended)

**Location**: `backend/app/tests/conftest.py`
**Insert after**: `db_story_with_simple_branch`

```python
@pytest.fixture(scope="function")
def db_story_with_deep_branch(db: Session) -> tuple[Story, UserStoryProgress]:
    """
    Create a story with nested branching (branch from branches).

    Structure:
        Start (2 choices)
        ├─ A → Node_A (2 choices)
        │   ├─ A1 → Node_A1 → A1_End
        │   └─ A2 → Node_A2 → A2_End
        └─ B → Node_B (2 choices)
            ├─ B1 → Node_B1 → B1_End
            └─ B2 → Node_B2 → B2_End

    Use cases:
    - Test state replay with complex branching
    - Test timeline navigation in deep trees
    - Test undo/jump with multiple branch points
    - Test that each path maintains independent state

    Returns:
        tuple[Story, UserStoryProgress]: Story and progress at start
    """
    # Similar implementation to db_story_with_simple_branch
    # but with 11 nodes and 10 choices
    # See implementation pattern above, create nested structure

    # Key: Create 2 branch points (Start, Node_A, Node_B)
    # Each branch point has 2 outgoing choices
    # Total 4 possible end states (A1_End, A2_End, B1_End, B2_End)

    pass  # Implementation follows same pattern as simple_branch
```

**Note**: Full implementation follows `db_story_with_simple_branch` pattern but creates deeper nesting.

---

## Migration Guide

### Step 1: Update test_event_sourcing.py Imports

No changes needed - tests already import from conftest.py

### Step 2: Update Test Signatures

**Current failing tests** in `test_event_sourcing.py`:

#### Tests needing `db_story_with_long_path`:

```python
# Lines 17-66
def test_snapshot_created_every_10_choices(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_long_path: tuple,  # ← Change from db_story_with_progress
):
    """Test that snapshots are created automatically every 10 choices."""
    story, progress = db_story_with_long_path  # ← Unpack tuple
    user_persona_id = progress.user_persona_id
    story_id = story.id
    # Rest of test unchanged
```

```python
# Lines 116-172
def test_replay_performance_with_snapshots(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_long_path: tuple,  # ← Change fixture
):
    """Test that replay with snapshots is faster than without."""
    story, progress = db_story_with_long_path  # ← Unpack
    user_persona_id = progress.user_persona_id
    story_id = story.id
    # Rest unchanged
```

```python
# Lines 286-324
def test_snapshot_coverage_metrics(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_long_path: tuple,  # ← Change fixture
):
    """Test snapshot coverage metrics calculation."""
    story, progress = db_story_with_long_path  # ← Unpack
    user_persona_id = progress.user_persona_id
    story_id = story.id
    # Rest unchanged
```

```python
# Lines 69-113
def test_replay_uses_snapshots(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_long_path: tuple,  # ← Change fixture (or create medium_path)
):
    """Test that replay uses snapshots when available."""
    story, progress = db_story_with_long_path  # ← Unpack
    user_persona_id = progress.user_persona_id
    story_id = story.id
    # Rest unchanged
```

#### Tests that can keep `db_story_with_progress`:

```python
# Lines 175-212
def test_state_always_derived_from_events(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,  # ← Keep as is (only needs 1 choice)
):
    """Test that story_state is ALWAYS derived from events, never mutated."""
    story, progress = db_story_with_progress
    # Rest unchanged
```

```python
# Lines 215-242
def test_undo_derives_state_from_events(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,  # ← Keep as is
):
    """Test that undo derives state from events (not mutable update)."""
    story, progress = db_story_with_progress
    # Rest unchanged
```

```python
# Lines 245-283
def test_jump_derives_state_from_events(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,  # ← Keep as is
):
    """Test that jump derives state from events (not mutable update)."""
    story, progress = db_story_with_progress
    # Rest unchanged
```

### Step 3: Verify Snapshot Logic Exists

**Critical Check**: After implementing fixtures, verify snapshot creation logic is implemented in the choice-making endpoint.

**Expected location**: `backend/app/api/routes/user_personas.py` or similar

**Expected logic**:
```python
# After making choice and updating head_choice_id
# Check if snapshot needed (every 10 choices)
chain_length = len(crud.get_choice_ancestor_chain(session, new_choice.id))
if chain_length % 10 == 0:
    # Create snapshot
    snapshot = ProgressSnapshot(
        progress_id=progress.id,
        choice_id=new_choice.id,
        snapshot_state=progress.story_state,
    )
    session.add(snapshot)
```

**If snapshot logic doesn't exist**: Tests will continue to fail even with correct fixtures.

---

## Testing Strategy

### Phase 1: Implement Long Path Fixture

1. **Add `db_story_with_long_path` to conftest.py**
2. **Update 4 tests in test_event_sourcing.py** to use new fixture
3. **Run tests**: `pytest backend/app/tests/test_event_sourcing.py -v`
4. **Expected result**:
   - If snapshot logic exists: Tests should pass
   - If snapshot logic missing: Tests fail at assertion but loop completes (makes 25+ choices)

### Phase 2: Verify Snapshot Logic

If tests still fail after fixture implementation:

1. **Search for snapshot creation**: `grep -r "ProgressSnapshot" backend/app/api/`
2. **Check choice endpoint**: Look in routes handling `POST /choices/{choice_id}`
3. **Implement snapshot logic** if missing (see Step 3 above)
4. **Re-run tests**

### Phase 3: Implement Branching Fixtures

1. **Add `db_story_with_simple_branch` to conftest.py**
2. **Create new test file**: `backend/app/tests/test_story_branching.py`
3. **Write branching tests** (examples below)
4. **Add `db_story_with_deep_branch`** if needed for complex tests

---

## Example Branching Tests

### Test File Template: `test_story_branching.py`

```python
"""Tests for story branching functionality."""

from fastapi.testclient import TestClient
from sqlmodel import Session


def test_start_node_has_multiple_choices(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_simple_branch: tuple,
) -> None:
    """
    Test that start node presents multiple available choices.

    Given: Story with branching start node
    When: GET current-node at start
    Then: Returns 2 available_choices
    """
    story, progress = db_story_with_simple_branch
    persona_id = progress.user_persona_id

    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["available_choices"]) == 2

    # Verify choices are distinct
    choice_texts = [c["text"] for c in data["available_choices"]]
    assert "left" in choice_texts[0].lower() or "right" in choice_texts[0].lower()
    assert "left" in choice_texts[1].lower() or "right" in choice_texts[1].lower()
    assert choice_texts[0] != choice_texts[1]


def test_different_choices_lead_to_different_nodes(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_simple_branch: tuple,
) -> None:
    """
    Test that taking different choices leads to different nodes.

    Given: Story with 2 choices from start
    When: User A takes choice 0, User B takes choice 1
    Then: They end up at different nodes with different content
    """
    story, progress = db_story_with_simple_branch
    persona_id = progress.user_persona_id

    # Get choices
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choices = response.json()["available_choices"]
    choice_0_id = choices[0]["id"]
    choice_1_id = choices[1]["id"]

    # Take choice 0
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_0_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Get current node after choice 0
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    node_after_choice_0 = response.json()

    # Undo to test other path
    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
        headers=normal_user_token_headers,
    )

    # Take choice 1
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_1_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Get current node after choice 1
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    node_after_choice_1 = response.json()

    # Verify different nodes
    assert node_after_choice_0["current_node"]["id"] != node_after_choice_1["current_node"]["id"]
    assert node_after_choice_0["current_node"]["title"] != node_after_choice_1["current_node"]["title"]


def test_branch_state_changes_differ(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_simple_branch: tuple,
) -> None:
    """
    Test that state changes differ based on which branch is taken.

    Given: Story with 2 branches setting different state
    When: Take left branch (sets path="left")
    Then: story_state contains {"path": "left"}
    When: Undo and take right branch (sets path="right")
    Then: story_state contains {"path": "right"}
    """
    story, progress = db_story_with_simple_branch
    persona_id = progress.user_persona_id

    # Get choices (assume [0]=left, [1]=right based on order)
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choices = response.json()["available_choices"]

    # Take first choice
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choices[0]['id']}",
        headers=normal_user_token_headers,
    )
    state_after_first = response.json()["story_state"]

    # Undo
    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
        headers=normal_user_token_headers,
    )

    # Take second choice
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choices[1]['id']}",
        headers=normal_user_token_headers,
    )
    state_after_second = response.json()["story_state"]

    # Verify states are different
    assert state_after_first != state_after_second
    assert "path" in state_after_first or "path" in state_after_second


def test_undo_from_branch_preserves_all_choices(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_simple_branch: tuple,
) -> None:
    """
    Test that undo from a branch returns to branch point with all choices available.

    Given: User takes left branch
    When: User undos back to start
    Then: Both left and right choices are still available
    """
    story, progress = db_story_with_simple_branch
    persona_id = progress.user_persona_id

    # Get initial choices
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    initial_choices = response.json()["available_choices"]
    assert len(initial_choices) == 2

    # Take first choice
    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{initial_choices[0]['id']}",
        headers=normal_user_token_headers,
    )

    # Undo
    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
        headers=normal_user_token_headers,
    )

    # Get choices after undo
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choices_after_undo = response.json()["available_choices"]

    # Verify all choices still available
    assert len(choices_after_undo) == 2
    # Choice IDs should match (order may differ)
    initial_ids = {c["id"] for c in initial_choices}
    after_undo_ids = {c["id"] for c in choices_after_undo}
    assert initial_ids == after_undo_ids
```

---

## Summary Checklist

### To Fix test_event_sourcing.py:

- [ ] Add `db_story_with_long_path` fixture to conftest.py
- [ ] Update 4 tests to use `db_story_with_long_path` instead of `db_story_with_progress`
- [ ] Run tests: `pytest backend/app/tests/test_event_sourcing.py -v`
- [ ] If still failing, verify snapshot creation logic exists in choice endpoint
- [ ] Implement snapshot logic if missing

### To Add Branching Tests:

- [ ] Add `db_story_with_simple_branch` fixture to conftest.py
- [ ] Create `backend/app/tests/test_story_branching.py`
- [ ] Copy test templates from above
- [ ] Run tests: `pytest backend/app/tests/test_story_branching.py -v`
- [ ] Optional: Add `db_story_with_deep_branch` for complex scenarios

---

## Cross-Reference Table

| Fixture | Used By | Purpose | Nodes | Choices | Branches |
|---------|---------|---------|-------|---------|----------|
| `db_story_with_progress` | `test_petri_timeline.py`<br>`test_story_timeline.py`<br>`test_user_story_tree.py` | Basic timeline/undo tests | 5 | 4 | 0 |
| `db_story_with_long_path` | `test_event_sourcing.py` (4 tests) | Snapshot interval testing | 60 | 59 | 0 |
| `db_story_with_simple_branch` | `test_story_branching.py` (new) | Basic branching tests | 5 | 4 | 1 |
| `db_story_with_deep_branch` | `test_story_branching.py` (new) | Complex branching tests | 11 | 10 | 4 |

---

**End of Implementation Guide**
