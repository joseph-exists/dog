# Pytest Fixture Error Reference Card

**Common Error:** `fixture 'session' not found`
**Root Cause:** Using wrong fixture name
**Quick Fix:** Use `db` instead of `session`

---

## Available Fixtures in conftest.py

### Database Session Fixtures

| Fixture Name | Type | Scope | Use Case |
|--------------|------|-------|----------|
| `db` | `Session` (sync) | `session` | **API/Integration tests** |
| `async_session` | `SQLModelAsyncSession` (async) | `function` | **Async/Agent tests** |

**❌ DOES NOT EXIST:** `session` fixture
**✅ USE INSTEAD:** `db` fixture for sync tests

---

## Error Pattern & Fix

### ❌ Wrong - Causes "fixture 'session' not found"

```python
def test_something(
    client: TestClient,
    session: Session,  # ❌ This fixture doesn't exist!
    normal_user_token_headers: dict[str, str],
) -> None:
    # Test code...
    pass
```

### ✅ Correct - Uses existing 'db' fixture

```python
def test_something(
    client: TestClient,
    db: Session,  # ✅ Use 'db' for sync session
    normal_user_token_headers: dict[str, str],
) -> None:
    # Test code...
    pass
```

---

## When to Use Which Fixture

### Use `db` (Sync Session) When:
- ✅ Testing API endpoints via `TestClient`
- ✅ Testing CRUD functions directly
- ✅ Setting up test data for API tests
- ✅ Integration tests that don't use async/await

**Example:**
```python
def test_create_story(
    client: TestClient,
    db: Session,  # ✅ Sync session for API test
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/stories",
        headers=superuser_token_headers,
        json={"title": "Test Story", "description": "Test"}
    )
    assert response.status_code == 200
```

### Use `async_session` (Async Session) When:
- ✅ Testing async agent functions
- ✅ Testing async database operations
- ✅ Tests using `async def` and `await`
- ✅ Tests with async fixtures (decorated with `@pytest_asyncio.fixture`)

**Example:**
```python
@pytest.mark.asyncio
async def test_agent_context(
    async_session: SQLModelAsyncSession,  # ✅ Async session for async test
    test_room: Room,
) -> None:
    # Async test code...
    result = await some_async_function(async_session, test_room)
    assert result is not None
```

---

## Quick Reference: Test File Patterns

### Pattern 1: API Integration Test (Sync)

```python
# File: test_stories.py

def test_list_stories(
    client: TestClient,           # HTTP client
    db: Session,                  # ✅ Sync DB session
    superuser_token_headers: dict[str, str],
) -> None:
    """Test listing stories via API."""
    response = client.get(
        f"{settings.API_V1_STR}/stories",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
```

### Pattern 2: Async Agent Test

```python
# File: test_agent_runner.py

@pytest.mark.asyncio
async def test_story_advisor_agent(
    async_session: SQLModelAsyncSession,  # ✅ Async DB session
    test_room_with_story: Room,
) -> None:
    """Test StoryAdvisor agent execution."""
    from app.services.agent_runner import run_agent_for_room_message

    result = await run_agent_for_room_message(
        room_id=test_room_with_story.room_id,
        message_content="Help me with my story",
        session=async_session
    )
    assert result is not None
```

### Pattern 3: Direct CRUD Test (Sync)

```python
# File: test_crud.py

def test_create_user_story_progress(
    db: Session,  # ✅ Sync session for CRUD test
) -> None:
    """Test CRUD function directly."""
    from app import crud
    from app.models import UserStoryProgressCreate

    progress_in = UserStoryProgressCreate(
        user_persona_id=uuid4(),
        story_id=uuid4(),
        story_version=1
    )

    progress = crud.create_user_story_progress(
        session=db,
        progress_in=progress_in
    )
    assert progress.head_version == 0
```

---

## Common Fixture Combinations

### API Test with DB Setup

```python
def test_api_endpoint_with_data(
    client: TestClient,
    db: Session,  # ✅ For setting up test data
    normal_user_token_headers: dict[str, str],
) -> None:
    # Setup: Create test data in DB
    from app.models import Story
    story = Story(
        id=uuid4(),
        title="Test",
        owner_id=uuid4()
    )
    db.add(story)
    db.commit()

    # Test: Call API
    response = client.get(
        f"{settings.API_V1_STR}/stories/{story.id}",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
```

### Test with Pre-built Fixture Data

```python
def test_with_fixture_data(
    client: TestClient,
    db: Session,  # ✅ Even if not used directly
    db_story_with_progress: tuple,  # Custom fixture that uses db
    normal_user_token_headers: dict[str, str],
) -> None:
    story, progress = db_story_with_progress

    response = client.get(
        f"{settings.API_V1_STR}/user-personas/{progress.user_persona_id}/stories/{story.id}/timeline",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
```

---

## Other Common Fixtures

### Authentication Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `superuser_token_headers` | `dict[str, str]` | Token headers for superuser |
| `normal_user_token_headers` | `dict[str, str]` | Token headers for normal user |

### Client Fixture

| Fixture | Type | Description |
|---------|------|-------------|
| `client` | `TestClient` | FastAPI test client for making HTTP requests |

### Custom Story Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `db_story_with_progress` | `tuple[Story, UserStoryProgress]` | Complete story setup with progress |
| `api_test_room` | `Room` | Test room for API tests |
| `api_test_room_with_agent` | `Room` | Test room with agent participant |

### Async Room Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `test_user` | `User` | Async test user |
| `test_story` | `Story` | Async test story |
| `test_room` | `Room` | Async test room |
| `test_room_with_story` | `Room` | Async room with story |
| `test_room_with_agent` | `Room` | Async room with agent |

---

## Troubleshooting Guide

### Error: "fixture 'session' not found"

**Root Cause:** Using `session` instead of `db`

**Fix:**
```python
# ❌ Wrong
def test_something(session: Session):
    pass

# ✅ Correct
def test_something(db: Session):
    pass
```

---

### Error: "fixture 'db' not found" (in async test)

**Root Cause:** Using sync fixture in async test

**Fix:**
```python
# ❌ Wrong
@pytest.mark.asyncio
async def test_something(db: Session):
    pass

# ✅ Correct
@pytest.mark.asyncio
async def test_something(async_session: SQLModelAsyncSession):
    pass
```

---

### Error: "coroutine was never awaited"

**Root Cause:** Missing `async`/`await` keywords

**Fix:**
```python
# ❌ Wrong
@pytest.mark.asyncio
def test_something(async_session: SQLModelAsyncSession):
    result = some_async_function()  # Missing await
    pass

# ✅ Correct
@pytest.mark.asyncio
async def test_something(async_session: SQLModelAsyncSession):
    result = await some_async_function()
    pass
```

---

### Error: Fixture has different scope than test

**Root Cause:** Mixing function-scoped and session-scoped fixtures incorrectly

**Understanding:**
- `db` fixture has `scope="session"` (shared across all tests)
- `async_session` has `scope="function"` (new for each test)
- Custom fixtures using `async_session` must also be function-scoped

**Fix:**
```python
# ❌ Wrong - scope mismatch
@pytest.fixture(scope="module")  # Module scope
def my_fixture(async_session: SQLModelAsyncSession):  # Function scope
    pass

# ✅ Correct - matching scopes
@pytest_asyncio.fixture(scope="function")
async def my_fixture(async_session: SQLModelAsyncSession):
    pass
```

---

## Migration Guide: Fixing Existing Tests

### Step 1: Identify the Pattern

Look at test signature:
```python
def test_something(session: Session, ...):  # ❌ Found 'session'
```

### Step 2: Determine Test Type

**Is it async?**
- Has `@pytest.mark.asyncio` decorator? → Use `async_session`
- Has `async def`? → Use `async_session`
- Otherwise → Use `db`

### Step 3: Replace Fixture

**For sync tests:**
```python
# Before
def test_something(session: Session, ...):
    story = session.get(Story, story_id)

# After
def test_something(db: Session, ...):
    story = db.get(Story, story_id)
```

**For async tests:**
```python
# Before
async def test_something(session: Session, ...):
    result = await session.exec(query)

# After
async def test_something(async_session: SQLModelAsyncSession, ...):
    result = await async_session.exec(query)
```

### Step 4: Update Function Calls

If test passes session to functions, update parameter names:
```python
# Before
def test_something(session: Session):
    crud.create_story(session=session, story_in=data)

# After
def test_something(db: Session):
    crud.create_story(session=db, story_in=data)
```

---

## Quick Fix Script

Use this grep command to find all instances:

```bash
# Find all tests using 'session: Session'
grep -r "session: Session" backend/app/tests/

# Find all tests that might need fixing
grep -r "def test.*session.*:" backend/app/tests/
```

**Automated fix with sed:**
```bash
# Backup first!
find backend/app/tests -name "*.py" -type f -exec sed -i.bak 's/session: Session/db: Session/g' {} \;

# Review changes
git diff backend/app/tests/

# If correct, remove backups
find backend/app/tests -name "*.py.bak" -delete
```

---

## Summary Checklist

When you see `fixture 'session' not found`:

- [ ] Check if test is sync or async
- [ ] Replace `session: Session` with `db: Session` (for sync tests)
- [ ] Replace `session: Session` with `async_session: SQLModelAsyncSession` (for async tests)
- [ ] Update all references inside test function (`session.get()` → `db.get()`)
- [ ] Ensure test decorator matches type (`@pytest.mark.asyncio` for async)
- [ ] Ensure test function signature matches (`def` for sync, `async def` for async)
- [ ] Run test to verify: `pytest backend/app/tests/path/to/test.py::test_name -v`

---

**End of Reference Card**

**Quick Answer:** Replace `session: Session` with `db: Session` in your test signatures!
