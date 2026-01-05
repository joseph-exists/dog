# Phase 1 Quick Reference Card - Event Tree Foundation

**Goal:** Add tree structure to UserNodeChoice and head pointer to UserStoryProgress (backward compatible)

**Estimated Time:** 1 week
**Branch:** `feature/cyoa-phase-1-event-tree`

---

## Pre-Implementation Checklist

- [X] Read CYOA_MIGRATION_PLAN.md Phase 1 section
- [X] Read CYOA_MIGRATION_ADDENDUM.md model patterns
- [X] Review existing UserNodeChoice and UserStoryProgress in `backend/app/models.py`
- [X] Ensure local dev environment is running (`docker compose up -d`)

---

## Step 1: Update Models (30 minutes)

### Location: `backend/app/models.py`

#### 1.1 Find UserNodeChoiceBase (around line 641)

**FIXED/IN FILE:**
```python
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
```

#### [x] COMPLETE 1.2 Add UserNodeChoiceCreate (after UserNodeChoiceBase)

```python
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
```

#### [x] DONE 1.3 Add UserNodeChoiceUpdate (after Create)

```python
class UserNodeChoiceUpdate(SQLModel):
    """
    Update model for UserNodeChoice.
    Note: In event sourcing, choices are immutable - this exists for consistency
    but should rarely/never be used.
    """
    choice_text: str | None = Field(default=None, max_length=500)  # type: ignore
    state_changes: dict[str, Any] | None = Field(default=None)
    rng_data: dict[str, Any] | None = Field(default=None)
```

#### [x] complete 1.4 Update UserNodeChoice Database Model

**Find existing UserNodeChoice (table=True) and ADD these fields:**

```python
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
```

#### [x] 1.5 Update UserNodeChoicePublic

```python
class UserNodeChoicePublic(UserNodeChoiceBase):
    """Public API response model for UserNodeChoice"""
    id: uuid.UUID
    progress_id: uuid.UUID
    parent_choice_id: uuid.UUID | None  # NEW in Phase 1
    choice_time: datetime
    rng_data: dict[str, Any] | None  # NEW in Phase 1
```

#### [x] 1.6 Update UserStoryProgressBase

**Find UserStoryProgressBase (around line 571) - NO CHANGES NEEDED**

Just verify it looks like this:
```python
class UserStoryProgressBase(SQLModel):
    """
    Base model for tracking a player's progress through a Story.
    This is the player's instance - locked to a specific story version.
    """
    current_node_id: uuid.UUID | None = Field(default=None)
    is_completed: bool = Field(default=False)

    # State accumulator - grows as player makes choices
    story_state: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
```

#### 1.7 Update UserStoryProgressUpdate

**Add new fields to existing UserStoryProgressUpdate:**

```python
class UserStoryProgressUpdate(SQLModel):
    """Input model for updating progress (all fields optional)"""
    current_node_id: uuid.UUID | None = Field(default=None)
    is_completed: bool | None = Field(default=None)
    story_state: dict[str, Any] | None = Field(default=None)

    # NEW in Phase 1 (for admin/debug only)
    head_choice_id: uuid.UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)
```

#### [x] 1.8 Update UserStoryProgress Database Model

**Find existing UserStoryProgress (table=True) and ADD these fields:**

```python
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
```

#### 1.9 Update UserStoryProgressPublic

```python
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
```

---

## Step 2: Add Relationships (15 minutes)

### Location: Bottom of `backend/app/models.py` (after all model definitions)

**Find the section with relationship definitions (around line 1468+)**

**Add this new section:**

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

## Step 3: Create Migration (20 minutes)

### 3.1 Enter Backend Container

```bash
docker compose exec backend bash
```

### 3.2 Create Migration

```bash
alembic revision --autogenerate -m "Add event tree structure to UserNodeChoice and UserStoryProgress"
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.autogenerate.compare] Detected added column 'usernodechoice.parent_choice_id'
INFO  [alembic.autogenerate.compare] Detected added column 'usernodechoice.rng_data'
INFO  [alembic.autogenerate.compare] Detected added column 'userstoryprogress.head_choice_id'
INFO  [alembic.autogenerate.compare] Detected added column 'userstoryprogress.head_version'
  Generating /app/app/alembic/versions/XXXX_add_event_tree_structure.py ...  done
```

### 3.3 Review Migration File

```bash
# Look for the new file in:
ls -lt app/alembic/versions/

# Open and review:
cat app/alembic/versions/XXXX_add_event_tree_structure*.py
```

**Verify migration includes:**
- ✅ `op.add_column('usernodechoice', sa.Column('parent_choice_id', ...)`
- ✅ `op.add_column('usernodechoice', sa.Column('rng_data', sa.JSON(), ...)`
- ✅ `op.add_column('userstoryprogress', sa.Column('head_choice_id', ...)`
- ✅ `op.add_column('userstoryprogress', sa.Column('head_version', sa.Integer(), ...)`
- ✅ Foreign key constraints for parent_choice_id and head_choice_id
- ✅ Index creation (may need to add manually if missing)

**If indexes missing, add this to migration file:**

```python
def upgrade() -> None:
    # ... existing add_column operations ...

    # Add indexes
    op.create_index('idx_usernodechoice_parent', 'usernodechoice', ['parent_choice_id'])
    op.create_index('idx_userstoryprogress_head', 'userstoryprogress', ['head_choice_id'])


def downgrade() -> None:
    # Add before drop_column operations:
    op.drop_index('idx_userstoryprogress_head', table_name='userstoryprogress')
    op.drop_index('idx_usernodechoice_parent', table_name='usernodechoice')

    # ... existing drop_column operations ...
```

### 3.4 Apply Migration

```bash
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade XXXX -> YYYY, Add event tree structure
```

### 3.5 Verify Migration

```bash
alembic current
```

**Should show:**
```
YYYY (head) add event tree structure to usernodechoice and userstoryprogress
```

### 3.6 Test Database Schema

```bash
# Connect to database
psql -U app -d app

# Check usernodechoice columns
\d usernodechoice

# Should see:
#  parent_choice_id | uuid
#  rng_data        | jsonb

# Check userstoryprogress columns
\d userstoryprogress

# Should see:
#  head_choice_id  | uuid
#  head_version    | integer

# Exit psql
\q

# Exit container
exit
```

---

## Step 4: Update Choice Endpoint (30 minutes)

### Location: `backend/app/api/routes/user_story_progress.py`

**Find `make_story_choice` function (around line 224)**

**MODIFY to add parent pointer:**

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
    Make a choice in the story and progress to the next node.

    MODIFIED in Phase 1: Appends choice with parent_choice_id for tree structure.
    """
    # ... existing validation code ...

    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    # ... existing checks ...

    # Create choice with parent pointer - MODIFIED
    user_choice = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=progress.head_choice_id,  # NEW: Link to parent
        choice_text=choice.text,
        from_node_id=choice.from_node_id,
        to_node_id=choice.to_node_id,
        state_changes=choice.sets_state,
        rng_data=None  # TODO: Phase 1 stub - capture RNG outcomes in future
    )
    session.add(user_choice)
    session.flush()  # Get ID

    # Update head pointer - NEW
    progress.head_choice_id = user_choice.id
    progress.head_version += 1
    progress.current_node_id = choice.to_node_id

    # UNCHANGED: Still update story_state mutably for backward compat
    if choice.sets_state:
        if progress.story_state:
            progress.story_state.update(choice.sets_state)
        else:
            progress.story_state = choice.sets_state

    # Check end node - UNCHANGED
    to_node = session.get(StoryNode, choice.to_node_id)
    if to_node and to_node.is_end_node:
        progress.is_completed = True

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

---

## Step 5: Write Tests (45 minutes)

### Location: `backend/app/tests/test_user_story_tree.py` (NEW FILE)

Create new test file:

```python
"""Tests for Phase 1: Event tree structure."""

import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import UserNodeChoice, UserStoryProgress


def test_choice_creates_parent_link(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,  # Assumes fixture exists
) -> None:
    """
    Test that making a choice sets parent_choice_id correctly.

    Given: A story progress at start (head_choice_id = None)
    When: Player makes first choice
    Then: New choice has parent_choice_id = None

    When: Player makes second choice
    Then: New choice has parent_choice_id = first_choice.id
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Get available choices
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    first_choice_id = data["available_choices"][0]["id"]

    # Make first choice
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{first_choice_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Verify first choice has parent_choice_id = None
    first_user_choice = session.exec(
        select(UserNodeChoice)
        .where(UserNodeChoice.progress_id == progress.id)
        .order_by(UserNodeChoice.choice_time)
    ).first()
    assert first_user_choice is not None
    assert first_user_choice.parent_choice_id is None

    # Make second choice
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    second_choice_id = response.json()["available_choices"][0]["id"]

    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{second_choice_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Verify second choice has parent_choice_id = first choice
    choices = session.exec(
        select(UserNodeChoice)
        .where(UserNodeChoice.progress_id == progress.id)
        .order_by(UserNodeChoice.choice_time)
    ).all()
    assert len(choices) == 2
    assert choices[1].parent_choice_id == choices[0].id


def test_head_pointer_updates(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that head_choice_id and head_version update correctly.

    Given: Progress at start (head_choice_id=None, head_version=0)
    When: Player makes choice
    Then: head_choice_id = new_choice.id, head_version = 1
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Verify initial state
    session.refresh(progress)
    assert progress.head_choice_id is None
    assert progress.head_version == 0

    # Make choice
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Verify head updated
    session.refresh(progress)
    assert progress.head_choice_id is not None
    assert progress.head_version == 1

    # Verify head points to the choice we made
    user_choice = session.get(UserNodeChoice, progress.head_choice_id)
    assert user_choice is not None
    assert user_choice.progress_id == progress.id


def test_rng_data_field_exists(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that rng_data field can be set (even if null in Phase 1).

    Given: A choice is made
    Then: UserNodeChoice has rng_data field (even if null)
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make choice
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Verify rng_data exists
    user_choice = session.exec(
        select(UserNodeChoice).where(UserNodeChoice.progress_id == progress.id)
    ).first()
    assert user_choice is not None
    assert hasattr(user_choice, "rng_data")
    # In Phase 1, this will be None
    assert user_choice.rng_data is None
```

### Run Tests

```bash
docker compose exec backend bash
pytest app/tests/test_user_story_tree.py -v
exit
```

---

## Step 6: Commit Changes (15 minutes)

```bash
# Check status
git status

# Should see:
#  modified: backend/app/models.py
#  modified: backend/app/api/routes/user_story_progress.py
#  new file: backend/app/alembic/versions/XXXX_add_event_tree_structure.py
#  new file: backend/app/tests/test_user_story_tree.py

# Stage changes
git add backend/app/models.py
git add backend/app/api/routes/user_story_progress.py
git add backend/app/alembic/versions/
git add backend/app/tests/test_user_story_tree.py

# Commit
git commit -m "feat: Add event tree structure for CYOA branching timelines (Phase 1)

- Add parent_choice_id to UserNodeChoice for tree structure
- Add rng_data field for deterministic replay
- Add head_choice_id and head_version to UserStoryProgress
- Update make_story_choice endpoint to set parent pointers
- Add Phase 1 tests for tree structure
- Add Alembic migration for schema changes

Refs: CYOA_MIGRATION_PLAN.md Phase 1"

# Push branch
git push origin feature/cyoa-phase-1-event-tree
```

---

## Step 7: Verify Backward Compatibility (15 minutes)

### 7.1 Test Existing Stories

```bash
# Start backend
docker compose up -d backend

# Run full test suite
docker compose exec backend bash
pytest app/tests/ -v

# Should see all existing tests PASS
# Especially: test_user_story_progress.py tests
```

### 7.2 Manual Testing

```bash
# Use API docs
open http://localhost:8000/docs

# Test flow:
# 1. POST /user-personas/{id}/stories/{story_id} - Start story
# 2. GET /user-personas/{id}/stories/{story_id}/current-node - Get position
# 3. POST /user-personas/{id}/stories/{story_id}/choices/{choice_id} - Make choice
# 4. GET /user-personas/{id}/stories/{story_id} - Verify head_choice_id updated
# 5. Repeat steps 2-4 to build a chain
```

### 7.3 Database Inspection

```bash
docker compose exec backend bash
psql -U app -d app

-- Check tree structure
SELECT
    id,
    parent_choice_id,
    choice_text,
    choice_time
FROM usernodechoice
WHERE progress_id = '<some-progress-id>'
ORDER BY choice_time;

-- Should see parent_choice_id forming a chain
-- First choice: parent_choice_id = NULL
-- Second choice: parent_choice_id = first_choice.id
-- Third choice: parent_choice_id = second_choice.id

\q
exit
```

---

## Troubleshooting

### Migration Fails

**Error:** `column "parent_choice_id" already exists`

**Solution:**
```bash
# Rollback migration
alembic downgrade -1

# Drop manually if needed
psql -U app -d app
ALTER TABLE usernodechoice DROP COLUMN IF EXISTS parent_choice_id;
ALTER TABLE usernodechoice DROP COLUMN IF EXISTS rng_data;
ALTER TABLE userstoryprogress DROP COLUMN IF EXISTS head_choice_id;
ALTER TABLE userstoryprogress DROP COLUMN IF EXISTS head_version;
\q

# Re-run migration
alembic upgrade head
```

### Tests Fail

**Error:** `AttributeError: 'UserNodeChoice' object has no attribute 'parent_choice_id'`

**Solution:**
- Ensure migration applied: `alembic current`
- Restart backend container: `docker compose restart backend`
- Re-run tests

### Foreign Key Constraint Error

**Error:** `insert or update on table "usernodechoice" violates foreign key constraint`

**Solution:**
- Ensure parent_choice_id points to valid UserNodeChoice.id in same progress
- Or set parent_choice_id = None for first choice

---

## Success Criteria

- [X] All new columns added to database
- [ ] Indexes created (idx_usernodechoice_parent, idx_userstoryprogress_head)
- [ ] Making choices creates tree structure (parent_choice_id links)
- [ ] head_choice_id and head_version update on each choice
- [ ] All existing tests pass
- [ ] New Phase 1 tests pass
- [ ] Backward compatible (existing stories work)
- [ ] Migration committed to git
- [ ] Code pushed to feature branch

---

## Estimated Time Breakdown

| Task | Time | Running Total |
|------|------|---------------|
| Update models | 30 min | 30 min |
| Add relationships | 15 min | 45 min |
| Create migration | 20 min | 1h 5min |
| Update endpoint | 30 min | 1h 35min |
| Write tests | 45 min | 2h 20min |
| Commit changes | 15 min | 2h 35min |
| Verify compatibility | 15 min | **2h 50min** |

**Buffer for issues:** +1h 10min
**Total with buffer:** ~4 hours

---

## Next Steps After Phase 1

Once Phase 1 is complete and merged:

1. **Create PR** to main branch
2. **Team review** of changes
3. **Merge** after approval
4. **Deploy** to staging environment
5. **Monitor** for issues
6. **Begin Phase 2** (Replay & Projection Logic)

---

## Quick Commands Reference

```bash
# Start dev environment
docker compose up -d

# Enter backend container
docker compose exec backend bash

# Create migration
alembic revision --autogenerate -m "message"

# Apply migration
alembic upgrade head

# Run tests
pytest app/tests/test_user_story_tree.py -v

# Check migration status
alembic current

# Database console
psql -U app -d app
```

---

## Support Resources

- **Main Plan:** `backend/docs/CYOA_MIGRATION_PLAN.md`
- **Patterns:** `backend/docs/CYOA_MIGRATION_ADDENDUM.md`
- **Backend Rules:** `backend/docs/RULES.md`
- **Data Models:** `backend/docs/data-model-best-practices.md`
- **Story System:** `backend/docs/STORY_SYSTEM.md`

**Questions?** Ping backend team or reference documents above.
