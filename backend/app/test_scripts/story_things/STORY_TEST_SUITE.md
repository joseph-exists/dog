# Story System Test Suite - Quick Start Guide

## What This Test Suite Does

The Story System Test Suite validates all CYOA (Choose Your Own Adventure) functionality including:
- **Phase 1-2:** Story creation, nodes, choices, progress tracking
- **Phase 3:** Timeline navigation (undo/jump/breadcrumbs)
- **Phase 4 Prep:** Event sourcing with parent pointers and replay logic

## Test Coverage (15 Tests)

### Story & Node Management (4 tests)
1. ✅ **Create Story** - Basic story creation with versioning
2. ✅ **Create Start Node** - Validates is_start_node flag
3. ✅ **Create Story Nodes** - Regular and end nodes
4. ✅ **Create Node Choices** - Choices with requirements and state changes

### Progress & Choice Making (4 tests)
5. ✅ **Start Story Progress** - UserStoryProgress creation, version locking
6. ✅ **Get Current Node** - Current position and available choices
7. ✅ **Make Choice** - Record choice, update state, move to next node
8. ✅ **State Changes Applied** - Verify story_state updates correctly

### Timeline Navigation - Phase 3 (4 tests)
9. ✅ **Undo Last Choice** - Move head to parent, state replay
10. ✅ **Jump to Ancestor** - Jump to arbitrary ancestor choice
11. ✅ **Jump to Start** - Jump back to story beginning
12. ✅ **Get Timeline** - Breadcrumb trail (root → head)

### Event Sourcing Validation (3 tests)
13. ✅ **Parent Choice Linkage** - Verify tree structure via parent_choice_id
14. ✅ **Head Version Increment** - Optimistic concurrency control
15. ✅ **State Replay Correctness** - Replayed state matches stored state

## Prerequisites

### 1. Existing `auth_helper.py`
This suite uses your existing `auth_helper.py` from the test_scripts directory.

Make sure it has: *this might be bad pattern, double check the authhelper*
```python
def get_authenticated_session(base_url: str) -> requests.Session:
    """Returns authenticated session"""

class AuthenticationError(Exception):
    """Raised when auth fails"""
```

### 2. Backend Stack Running
```bash
# Start full stack
docker compose up -d

# Or just backend + database
docker compose up -d backend db
```

### 3. Test User
Ensure your test user credentials are configured in `test.env`:
```bash
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=yourpassword
```

### 4. User Persona
The test suite will create a test persona automatically, or you can specify one:
```bash
# Optional: Specify existing persona ID
export TEST_PERSONA_ID=your-persona-uuid
```

## How to Run

```bash
cd backend/app/test_scripts

# Run the full test suite
python test_story_system.py

# Run with verbose output
python test_story_system.py --verbose

# Run specific test phase
python test_story_system.py --phase 1  # Story/Node CRUD only
python test_story_system.py --phase 2  # Progress & Choices only
python test_story_system.py --phase 3  # Timeline Navigation only
```

## Expected Output

### ✅ All Tests Pass (Complete Implementation)

```
======================================================================
  STORY SYSTEM TEST SUITE
  CYOA Phase 1-3 Validation
======================================================================

──────────────────────────────────────────────────────────────────────
  Authentication
──────────────────────────────────────────────────────────────────────
  Authenticating with backend...
  ✅ Authentication successful!
  👤 User: test@example.com (ID: 12345678...)

──────────────────────────────────────────────────────────────────────
  Test Setup: Creating Test Persona
──────────────────────────────────────────────────────────────────────
  ✅ Test persona created: "Test Explorer" (ID: 12345678...)

──────────────────────────────────────────────────────────────────────
  PHASE 1: Story & Node Management
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
  Test 1: Create Story
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: create_story
     Story created: "The Enchanted Forest" (ID: 12345678...)
     Current version: 1
     Creator: test@example.com

──────────────────────────────────────────────────────────────────────
  Test 2: Create Start Node
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: create_start_node
     Start node: "Forest Entrance" (ID: 12345678...)
     is_start_node: true
     Story version: 1

──────────────────────────────────────────────────────────────────────
  Test 3: Create Story Nodes
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: create_story_nodes
     Created 3 nodes:
       - "The Crossroads" (regular)
       - "The Dark Cave" (regular)
       - "Victory!" (end node)

──────────────────────────────────────────────────────────────────────
  Test 4: Create Node Choices
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: create_node_choices
     Created 4 choices:
       - "Go left" (Forest Entrance → Crossroads)
       - "Go right" (Forest Entrance → Dark Cave)
       - "Enter cave" (Crossroads → Dark Cave, requires: courage > 5)
       - "Find treasure" (Dark Cave → Victory, sets: has_treasure = true)

──────────────────────────────────────────────────────────────────────
  PHASE 2: Progress & Choice Making
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
  Test 5: Start Story Progress
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: start_story_progress
     Progress created for persona "Test Explorer"
     Locked to story version: 1
     Starting node: "Forest Entrance"
     head_version: 0 (at start)
     head_choice_id: null

──────────────────────────────────────────────────────────────────────
  Test 6: Get Current Node
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: get_current_node
     Current node: "Forest Entrance"
     Available choices: 2
       - "Go left"
       - "Go right"

──────────────────────────────────────────────────────────────────────
  Test 7: Make Choice
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: make_choice
     Choice made: "Go left"
     New node: "The Crossroads"
     head_version: 1 (incremented)
     head_choice_id: 12345678... (first choice)

──────────────────────────────────────────────────────────────────────
  Test 8: State Changes Applied
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: state_changes_applied
     Made choice: "Find treasure"
     story_state: {"has_treasure": true}
     State correctly updated

──────────────────────────────────────────────────────────────────────
  PHASE 3: Timeline Navigation
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
  Test 9: Undo Last Choice
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: undo_last_choice
     Undid: "Find treasure"
     Back to node: "The Dark Cave"
     head_version: 4 (incremented on undo)
     story_state: {} (state correctly replayed)

──────────────────────────────────────────────────────────────────────
  Test 10: Jump to Ancestor
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: jump_to_ancestor
     Jumped from choice #3 to choice #1
     Current node: "The Crossroads"
     head_version: 5 (incremented on jump)
     Abandoned branch hidden (choices #2, #3 not in timeline)

──────────────────────────────────────────────────────────────────────
  Test 11: Jump to Start
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: jump_to_start
     Jumped to story start
     Current node: "Forest Entrance"
     head_choice_id: null
     head_version: 6

──────────────────────────────────────────────────────────────────────
  Test 12: Get Timeline
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: get_timeline
     Timeline events: 3
       - Story Start (is_current: false)
       - "Go left" (is_current: false)
       - "Enter cave" (is_current: true)
     head_version: 2
     Active path only (no abandoned branches)

──────────────────────────────────────────────────────────────────────
  PHASE 4 PREP: Event Sourcing Validation
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
  Test 13: Parent Choice Linkage
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: parent_choice_linkage
     Choice #1: parent_choice_id = null (root)
     Choice #2: parent_choice_id = choice #1 (linked)
     Choice #3: parent_choice_id = choice #2 (linked)
     Tree structure validated

──────────────────────────────────────────────────────────────────────
  Test 14: Head Version Increment
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: head_version_increment
     Initial: head_version = 0
     After choice: head_version = 1 (+1)
     After undo: head_version = 2 (+1)
     After jump: head_version = 3 (+1)
     Monotonically increasing ✓

──────────────────────────────────────────────────────────────────────
  Test 15: State Replay Correctness
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: state_replay_correctness
     Using /validate-state endpoint
     Stored state: {"courage": 10, "has_treasure": true}
     Replayed state: {"courage": 10, "has_treasure": true}
     ✓ States match (replay logic correct)

======================================================================
  TEST SUMMARY
======================================================================

  Total Tests:  15
  ✅ Passed:    15
  ❌ Failed:    0
  Success Rate: 100.0%

💾 Results saved to: test_results_story_system.json

🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
  ALL TESTS PASSED!
🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉

  ✅ Story system (Phases 1-3) is working correctly
  ✅ Timeline navigation fully functional
  ✅ Event sourcing foundations validated
  ✅ Ready for Phase 4 (Real-time distribution)
```

### ❌ Common Failures & Debugging

#### Test 7 Fails: "Make Choice"
```
──────────────────────────────────────────────────────────────────────
  Test 7: Make Choice
──────────────────────────────────────────────────────────────────────
  ❌ FAILED: make_choice
     HTTP 500: {"detail":"'UserNodeChoice' object has no attribute 'parent_choice_id'"}

  🚨 MISSING FIELD: parent_choice_id not in UserNodeChoice model!
     → Run Phase 1 migration to add parent_choice_id column
     → See CYOA_MIGRATION_PLAN.md Section 1.1
```

**Fix:**
```bash
cd backend
alembic revision --autogenerate -m "Add parent_choice_id to UserNodeChoice"
alembic upgrade head
```

#### Test 9 Fails: "Undo Last Choice"
```
──────────────────────────────────────────────────────────────────────
  Test 9: Undo Last Choice
──────────────────────────────────────────────────────────────────────
  ❌ FAILED: undo_last_choice
     HTTP 404: {"detail":"Not Found"}

  🚨 ENDPOINT MISSING: POST /stories/{id}/undo not implemented!
     → Implement undo endpoint from Phase 3
     → See CYOA_MIGRATION_PLAN.md Section 3.1
```

**Fix:**
Implement the `/undo` endpoint in `user_story_progress.py`.

#### Test 15 Fails: "State Replay Correctness"
```
──────────────────────────────────────────────────────────────────────
  Test 15: State Replay Correctness
──────────────────────────────────────────────────────────────────────
  ❌ FAILED: state_replay_correctness
     State mismatch detected!
     Stored:   {"courage": 10, "has_treasure": true}
     Replayed: {"courage": 10}

     Missing in replay: has_treasure

  🚨 REPLAY LOGIC ERROR: State replay not including all changes!
     → Check replay_state_from_head() function
     → Verify all choices in ancestor chain are processed
```

**Fix:**
Check the `replay_state_from_head()` implementation in `crud.py`.

## Bug Detection Features

The test suite automatically detects:

- **"Missing parent_choice_id"** → Phase 1 migration not applied
- **"Endpoint not found (undo/jump/timeline)"** → Phase 3 not implemented
- **"head_version not incrementing"** → Optimistic concurrency not working
- **"State mismatch"** → Replay logic bug
- **"parent_choice_id is null for child"** → Tree structure not linking correctly

## Test Data Created

The test suite creates:
- 1 test story: "The Enchanted Forest"
- 4 story nodes (1 start, 2 regular, 1 end)
- 4 node choices with various requirements
- 1 user story progress
- ~6-8 user node choices (depending on test execution path)

**Cleanup:**
All test data uses unique names (timestamped) and won't conflict with existing data. You can manually clean up via:
```bash
# Find test stories
curl http://localhost:8000/api/v1/stories?search=The%20Enchanted%20Forest

# Delete test story (cascade deletes nodes, choices, progress)
curl -X DELETE http://localhost:8000/api/v1/stories/{story_id}
```

## Results File

The script creates `test_results_story_system.json`:

```json
{
  "test_suite": "Story System Test Suite",
  "start_time": "2026-01-02T14:30:00.000000",
  "end_time": "2026-01-02T14:30:45.123456",
  "duration_seconds": 45.12,
  "phases": {
    "phase_1": {
      "name": "Story & Node Management",
      "tests": 4,
      "passed": 4,
      "failed": 0
    },
    "phase_2": {
      "name": "Progress & Choice Making",
      "tests": 4,
      "passed": 4,
      "failed": 0
    },
    "phase_3": {
      "name": "Timeline Navigation",
      "tests": 4,
      "passed": 4,
      "failed": 0
    },
    "validation": {
      "name": "Event Sourcing Validation",
      "tests": 3,
      "passed": 3,
      "failed": 0
    }
  },
  "total_tests": 15,
  "passed": 15,
  "failed": 0,
  "success_rate": "100.0%",
  "test_entities": {
    "story_id": "12345678-...",
    "persona_id": "12345678-...",
    "progress_id": "12345678-...",
    "node_ids": ["...", "...", "..."],
    "choice_ids": ["...", "...", "..."]
  },
  "tests": [
    {
      "name": "create_story",
      "phase": "phase_1",
      "passed": true,
      "message": "Story created: The Enchanted Forest",
      "timestamp": "2026-01-02T14:30:05.000000"
    },
    ...
  ]
}
```

## Advanced Usage

### Run with Custom Persona

```bash
# Use existing persona instead of creating test persona
python test_story_system.py --persona-id YOUR-PERSONA-UUID
```

### Skip Cleanup

```bash
# Keep test data after run (for inspection)
python test_story_system.py --no-cleanup
```

### Test Specific Phases

```bash
# Only test story/node creation (Phase 1)
python test_story_system.py --phase 1

# Only test timeline navigation (Phase 3)
python test_story_system.py --phase 3
```

### Export Test Story

```bash
# Save test story definition to JSON
python test_story_system.py --export-story story_export.json
```

## What to Fix Based on Failures

### Phase 1 Failures
- Missing models: Check `models.py` has Story, StoryNode, NodeChoice
- Missing migrations: Run `alembic upgrade head`
- Missing CRUD functions: Check `crud.py` has story CRUD operations

### Phase 2 Failures
- Missing UserStoryProgress model
- Missing `replay_state_from_head()` function
- Choice endpoint not updating head_choice_id

### Phase 3 Failures
- Missing `/undo` endpoint
- Missing `/jump` endpoint
- Missing `/timeline` endpoint
- `move_head_to_choice()` helper not implemented

### Validation Failures
- Replay logic not aggregating state correctly
- Parent pointers not being set
- Head version not incrementing

## Integration with CI/CD

### GitHub Actions

```yaml
name: Story System Tests

on: [push, pull_request]

jobs:
  test-story-system:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start backend stack
        run: docker compose up -d --wait

      - name: Run story system tests
        run: |
          cd backend/app/test_scripts
          python test_story_system.py

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: story-test-results
          path: backend/app/test_scripts/test_results_story_system.json
```

## Estimated Run Time

- **Phase 1-2 (Story/Progress):** 10-15 seconds
- **Phase 3 (Timeline):** 5-10 seconds
- **Validation:** 5 seconds
- **Total (all phases):** 20-30 seconds

## Next Steps After All Tests Pass

1. ✅ Commit story system implementation
2. ✅ Proceed to Phase 4: Real-time distribution (Redis pub/sub)
3. ✅ Implement WebSocket endpoint for story updates
4. ✅ Add real-time event publishing to choice/undo/jump endpoints
5. ✅ Test with multiple concurrent users

## Related Documentation

- `backend/docs/CYOA_MIGRATION_PLAN.md` - Implementation roadmap
- `backend/docs/CYOA_PHASE4_QUICKREF.md` - Phase 4 real-time guide
- `backend/docs/EVENT_SYSTEMS_ALIGNMENT.md` - Room vs Story event patterns
- `backend/app/test_scripts/ROOM_TEST.md` - Room system test suite (similar pattern)

---

**Questions or Issues?**
- Check backend logs: `docker compose logs backend`
- Verify database migrations: `docker compose exec backend alembic current`
- Test authentication: `python auth_helper.py`
- Review API docs: `http://localhost:8000/docs`
