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

#### [x] 1.1 Find UserNodeChoiceBase (around line 641)

#### [x] COMPLETE 1.2 Add UserNodeChoiceCreate (after UserNodeChoiceBase)


#### [x] DONE 1.3 Add UserNodeChoiceUpdate (after Create)


#### [x] complete 1.4 Update UserNodeChoice Database Model



#### [x] 1.5 Update UserNodeChoicePublic


#### [x] 1.6 Update UserStoryProgressBase




#### [x]  1.7 Update UserStoryProgressUpdate



#### [x] 1.8 Update UserStoryProgress Database Model


#### [x] 1.9 Update UserStoryProgressPublic



## [x] Step 2: Add Relationships (15 minutes)

### Location: Bottom of `backend/app/models.py` (after all model definitions)
#### Phase 1: Event Tree Relationships


## [x] Step 3: Create Migration (20 minutes)

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

** `make_story_choice` function modified to add parent pointer:**



---

## Step 5: Tests

### Location: `backend/app/tests/test_user_story_tree.py` (NEW FILE)

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
- [X] Indexes created (idx_usernodechoice_parent, idx_userstoryprogress_head)
- [X] Making choices creates tree structure (parent_choice_id links)
- [X] head_choice_id and head_version update on each choice
- [X] All existing tests pass
- [X] New Phase 1 tests pass
- [X] Backward compatible (existing stories work)
- [X] Migration committed to git
- [X] Code pushed to feature branch

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
