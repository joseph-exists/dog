# Room Unit Tests - Quick Start Guide

## What This Script Does

`test_room_unit.py` is a comprehensive unit test suite that verifies all Phase 1 Room Management functionality and specifically catches the bugs we identified in the review.

## Test Coverage (10 Tests)

1. ✅ **Create Room** - Basic room creation
2. ✅ **Creator is Owner** - Verifies event sourcing (room.created + participant.joined)
3. ✅ **Add Agent Participant** - Tests adding agents to rooms
4. ✅ **Send User Message** - **CRITICAL: Catches Bug #1 (event type mismatch)**
5. ✅ **List Messages** - **CRITICAL: Catches Bug #4 (variable name bug)**
6. ✅ **Message Pagination** - Tests cursor-based pagination
7. ✅ **Change Participant Role** - Tests role changes (member → owner)
8. ✅ **Remove Participant** - Tests soft delete (active=False)
9. ✅ **Update Room** - Tests room metadata updates
10. ✅ **List User's Rooms** - Tests room listing for user

## Prerequisites

### 1. Existing `auth_helper.py`
This script uses your existing `auth_helper.py` (the one from `populate_jungian_system.py`).

Make sure `auth_helper.py` is in the same directory and has:
```python
def get_authenticated_session(base_url: str) -> requests.Session:
    """Returns authenticated session"""
    
class AuthenticationError(Exception):
    """Raised when auth fails"""
```

### 2. Backend Running
```bash
cd backend
uvicorn app.main:app --reload
```

### 3. Test User
Ensure your test user credentials are configured in `auth_helper.py`.

## How to Run

```bash
# Place both files in same directory
# - test_room_unit.py
# - auth_helper.py (your existing one)

python test_room_unit.py
```

## Expected Output

### ✅ All Tests Pass (After Bug Fixes)
```
======================================================================
  ROOM SYSTEM UNIT TESTS
  Phase 1 Bug Verification & Core Functionality
======================================================================

──────────────────────────────────────────────────────────────────────
  Authentication
──────────────────────────────────────────────────────────────────────
  Authenticating with backend...
  ✅ Authentication successful!
  👤 User: test@example.com (ID: 12345678...)

──────────────────────────────────────────────────────────────────────
  Test 1: Create Room
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: create_room
     Room created: Test Room - Basic Creation (ID: 12345678...)

──────────────────────────────────────────────────────────────────────
  Test 2: Creator Auto-Added as Owner
──────────────────────────────────────────────────────────────────────
  ✅ PASSED: creator_is_owner
     Creator has role='owner' and active=True

[... more tests ...]

======================================================================
  TEST SUMMARY
======================================================================

  Total Tests:  10
  ✅ Passed:    10
  ❌ Failed:    0
  Success Rate: 100.0%

💾 Results saved to: test_results_room_unit_tests.json

🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
  ALL TESTS PASSED!
🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉

  ✅ All Phase 1 bugs are fixed
  ✅ Room system is working correctly
  ✅ Ready for integration testing
```

### ❌ Tests Fail (Before Bug Fixes)

#### Bug #1: Event Type Mismatch
```
──────────────────────────────────────────────────────────────────────
  Test 4: Send User Message (Bug #1 Check)
──────────────────────────────────────────────────────────────────────
  This test verifies the event type fix: 'message.user' not 'room_message.user'
  ❌ FAILED: send_user_message
     HTTP 500: {"detail":"Unsupported event type: room_message.user"}

  🚨 BUG DETECTED: Event type mismatch!
     The CRUD layer is emitting 'room_message.user'
     but the event handler expects 'message.user'
     → Fix Bug #1 in send_user_message() function
```

#### Bug #4: Variable Name Mismatch
```
──────────────────────────────────────────────────────────────────────
  Test 5: List Messages (Bug #4 Check)
──────────────────────────────────────────────────────────────────────
  This test verifies the variable name fix: 'messages' not 'room_messages'
  ❌ FAILED: list_messages
     HTTP 500: {"detail":"NameError: name 'room_messages' is not defined"}

  🚨 BUG DETECTED: Variable name mismatch!
     The function is trying to use 'room_messages'
     but the variable is named 'messages'
     → Fix Bug #4 in list_room_messages() return statement
```

## Bug Detection Features

The script automatically detects and explains specific bugs:

- **"Unsupported event type"** → Points to Bug #1 with fix location
- **"NameError: room_messages"** → Points to Bug #4 with fix location
- **"NameError: Message"** → Would catch Bug #2 (model class)

## Results File

The script creates `test_results_room_unit_tests.json` with detailed results:

```json
{
  "test_name": "Room System Unit Tests",
  "start_time": "2025-12-18T10:00:00.000000",
  "end_time": "2025-12-18T10:00:15.234567",
  "duration_seconds": 15.23,
  "total_tests": 10,
  "passed": 10,
  "failed": 0,
  "success_rate": "100.0%",
  "tests": [
    {
      "name": "create_room",
      "passed": true,
      "message": "Room created: Test Room - Basic Creation (ID: 12345678...)",
      "timestamp": "2025-12-18T10:00:01.123456"
    },
    ...
  ]
}
```

## What to Fix Based on Failures

### If "send_user_message" fails:
```python
# In send_user_message() function (crud.py or big-review.py):
await emit_event(
    session=session,
    room_id=room_id,
    event_type="message.user",  # ✅ Change from "room_message.user"
    payload={
        "sender_id": str(user_id),
        "content": content,
    },
)
```

### If "list_messages" fails:
```python
# In list_room_messages() function:
result = await session.execute(query)
messages = result.scalars().all()  # ← Variable name

return RoomMessagesPublic(
    data=[RoomMessagePublic.model_validate(msg) for msg in messages],  # ✅ Use 'messages'
    count=total_count,
)
```

## Quick Debugging

### Backend logs not showing?
```bash
# Run backend with more logging
uvicorn app.main:app --reload --log-level debug
```

### Can't authenticate?
```bash
# Test auth_helper directly
python -c "from auth_helper import get_authenticated_session; get_authenticated_session('http://localhost:8000/api/v1')"
```

### Tests hang?
- Check backend is running: `curl http://localhost:8000/docs`
- Check database is accessible
- Check no other process is blocking port 8000

## After All Tests Pass

Once you see the 🎉 celebration, you're ready for:

1. ✅ Commit your bug fixes
2. ✅ Run integration tests (if you have populate_room_system.py)
3. ✅ Proceed to Phase 2: Agent Integration

## Estimated Run Time

- With all bugs fixed: **10-15 seconds**
- With network delays: **20-30 seconds**

## Next Steps

After unit tests pass, you can:

1. Create more comprehensive integration tests
2. Test multi-user scenarios
3. Test concurrent operations
4. Begin Phase 2 agent integration

---

**Note:** This script is designed to be run repeatedly as you fix bugs. Each run gives you immediate feedback on which bugs are fixed and which remain.