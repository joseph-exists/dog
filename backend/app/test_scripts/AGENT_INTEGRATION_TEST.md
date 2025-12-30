# Agent Integration Test - Quick Start Guide

## What This Script Does

`test_agent_integration.py` is a comprehensive end-to-end test that verifies all Phase 2 Agent Integration functionality:

- ✅ Agent registration and discovery
- ✅ Room creation with agent participants
- ✅ Automatic agent responses to user messages
- ✅ Agent context awareness (story, messages, participants)
- ✅ Event persistence and message retrieval
- ✅ Full transaction support (user message + agent response atomic)

## Test Flow (9 Steps)

1. **Authentication** - Validates user credentials
2. **Create Test Story** (optional) - Sets up story context for agent
3. **Create Room** - Creates a collaborative room
4. **Add StoryAdvisor Agent** - Adds agent as room participant
5. **Send Initial Message** - Triggers agent with a question
6. **Verify Agent Response** - Confirms agent replied
7. **Test Story Context** - Verifies agent knows about the story
8. **Test Message History** - Verifies agent remembers conversation
9. **Validate Persistence** - Confirms all messages are saved

## Prerequisites

### 1. Existing `auth_helper.py`
This script uses your existing `auth_helper.py` from other test scripts.

Make sure `auth_helper.py` is in the same directory and has:
```python
def get_authenticated_session() -> requests.Session:
    """Returns authenticated session"""

class AuthenticationError(Exception):
    """Raised when auth fails"""
```

### 2. Backend Running with Agents
```bash
cd backend
# Make sure OPENAI_API_KEY is set in .env
source .venv/bin/activate
fastapi dev app/main.py
```

**Important:** The backend must have a valid `OPENAI_API_KEY` set in the `.env` file for the StoryAdvisor agent to function.

### 3. Test User
Ensure your test user credentials are configured in `auth_helper.py`.

## How to Run

### Basic Test (with story context)
```bash
cd backend/app/test_scripts
python test_agent_integration.py
```

### Test Without Story
```bash
python test_agent_integration.py --no-story
```

### Custom Room Title
```bash
python test_agent_integration.py --room-title "My Agent Test"
```

### Custom Output File
```bash
python test_agent_integration.py --output my_test_results.json
```

### Enable Debug Logging
```bash
python test_agent_integration.py --debug
```

The `--debug` flag enables verbose logging that shows:
- Message counts before and after sending
- Whether agent responded synchronously (during request) or asynchronously
- Poll-by-poll progress when waiting for agent responses
- Content preview of latest messages during polling

This is helpful for diagnosing timing issues or understanding agent response patterns.

## Expected Output

### ✅ All Tests Pass

```
🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖
  PHASE 2: AGENT INTEGRATION TEST
🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖

======================================================================
[1/9] Authentication
----------------------------------------------------------------------
  ✅ Authenticated as: user@example.com

======================================================================
[2/9] Creating Test Story
----------------------------------------------------------------------
  ✅ Created story: The Quest for the Ancient Scroll
     ID: abc123...

======================================================================
[3/9] Creating Room
----------------------------------------------------------------------
  ✅ Created room: Agent Integration Test Room
     ID: def456...
     Linked to story: The Quest for the Ancient Scroll

======================================================================
[4/9] Adding StoryAdvisor Agent as Participant
----------------------------------------------------------------------
  ✅ Added agent: StoryAdvisor
     Type: agent
     Role: member
  📊 Room participants: 2 total, 1 agents

======================================================================
[5/9] Sending Initial Message to Trigger Agent
----------------------------------------------------------------------
  ✅ Sent message: Hello! I'm working on my story and need some advice...
     Message ID: ghi789...
  ⏳ Waiting for agent response (max 15s)...
  ✅ Agent responded in 3s

======================================================================
[6/9] Verifying Agent Response
----------------------------------------------------------------------
  📊 Total messages: 2
  🤖 Agent messages: 1
  ✅ Agent response received:
     From: StoryAdvisor
     Content: I'd be happy to help with your story's pacing! Opening chapters are crucial...

======================================================================
[7/9] Testing Context Awareness - Story Context
----------------------------------------------------------------------
  ⏳ Waiting for agent response (max 15s)...
  ✅ Agent responded in 2s
  ✅ Agent demonstrated story context awareness

======================================================================
[8/9] Testing Context Awareness - Message History
----------------------------------------------------------------------
  ⏳ Waiting for agent response (max 15s)...
  ✅ Agent responded in 3s
  ✅ Agent demonstrated message history awareness

======================================================================
[9/9] Validating Event Persistence
----------------------------------------------------------------------
  ✅ Messages persisted and retrieved
     Total messages: 6
     User messages: 3
     Agent messages: 3

======================================================================
  Test Summary
======================================================================
  ⏱️  Duration: 12.45 seconds

  📊 Test Results:
    • Authentication:     ✅ success
    • Story Creation:     ✅ success
    • Room Creation:      ✅ success
    • Agent Participant:  ✅ success

  💬 Messages:
    • User messages sent:        3
    • Agent responses received:  3

  🧠 Context Awareness:
    • Story Context Test: ✅ success
    • Message History Test: ✅ success
    • Participant Awareness Test: ✅ success

  💾 Persistence:
    • Events persisted:  6
    • Messages retrieved: 6

  ✅ No errors encountered

💾 Results saved to: test_results_agent_integration.json

🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
  AGENT INTEGRATION TEST PASSED!
🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
```

## Test Results File

The script generates a detailed JSON results file: `test_results_agent_integration.json`

### Sample Results Structure
```json
{
  "test_run": {
    "start_time": "2025-12-27T14:30:00.000000",
    "end_time": "2025-12-27T14:30:12.450000",
    "duration_seconds": 12.45,
    "success": true,
    "phase": "Phase 2: Agent Integration"
  },
  "authentication": {
    "status": "success",
    "user": {
      "email": "user@example.com",
      "id": "..."
    }
  },
  "story": {
    "status": "success",
    "story_id": "abc123...",
    "title": "The Quest for the Ancient Scroll"
  },
  "room": {
    "status": "success",
    "room_id": "def456...",
    "title": "Agent Integration Test Room"
  },
  "agent_participant": {
    "status": "success",
    "agent_name": "StoryAdvisor",
    "participant_id": "StoryAdvisor"
  },
  "messages": {
    "user_messages_sent": 3,
    "agent_responses_received": 3,
    "messages": [...]
  },
  "context_awareness": {
    "story_context_test": {
      "status": "success",
      "passed": true,
      "details": "Agent did reference story context"
    },
    "message_history_test": {
      "status": "success",
      "passed": true,
      "details": "Agent did reference message history"
    }
  },
  "persistence": {
    "event_count": 6,
    "messages_persisted": true,
    "messages_retrieved": [...]
  },
  "errors": []
}
```

## What's Being Tested

### ✅ Core Functionality
- Agent registration via `AGENT_REGISTRY`
- Agent participant management in rooms
- Automatic agent triggering on user messages
- Agent response generation and persistence

### ✅ Context Awareness
- **Story Context**: Agent can access and reference story details
- **Message History**: Agent remembers previous conversation
- **Participant Awareness**: Agent knows who's in the room

### ✅ Transaction Support
- User message and agent response are atomic
- All events are properly persisted
- Messages can be retrieved and replayed

### ✅ Event Sourcing
- `room.created` event
- `participant.joined` events (user + agent)
- `room_message.user` events
- `room_message.agent` events

## Troubleshooting

### Agent Doesn't Respond
**Problem:** Test times out waiting for agent response

**Solutions:**
1. Check `OPENAI_API_KEY` is set in `.env`
2. Verify agent is registered: `curl http://localhost:8000/api/v1/rooms/{room_id}/participants`
3. Check backend logs for errors
4. Ensure sufficient OpenAI API credits

### Authentication Fails
**Problem:** `AuthenticationError` during test

**Solution:** Check `auth_helper.py` credentials match your test user

### "Agent not registered" Error
**Problem:** Agent isn't found in `AGENT_REGISTRY`

**Solution:**
1. Verify `app/agents/__init__.py` imports `story_advisor`
2. Check `app/main.py` imports `app.agents`
3. Restart the backend to trigger agent registration

### Context Tests Fail
**Problem:** Agent responses don't show context awareness

**Expected:** This can happen if:
- Agent's system prompt isn't properly configured
- Context provider isn't loading data correctly
- OpenAI API returns generic responses

**Check:** Review agent responses in the JSON output to verify they make sense

### Important Implementation Note
**Message Ordering**: The API returns messages in **descending order** (newest first). The test script has been updated to correctly handle this by accessing `messages[0]` for the latest message, not `messages[-1]` which would be the oldest message. If you're writing your own integration tests, be aware of this ordering.

## Next Steps

After this test passes:

1. ✅ **Phase 2 Complete** - All agent integration functionality is working
2. 🚀 **Production Ready** - Agent system is ready for real use
3. 📝 **Add More Agents** - Follow the StoryAdvisor pattern to create new agents
4. 🎨 **Frontend Integration** - Connect UI to display agent messages

## Architecture Validated

This test confirms:

```
┌─────────────┐
│  User sends │
│   message   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  POST /rooms/{id}/messages      │
│  (app/api/routes/rooms.py:316)  │
└──────┬──────────────────────────┘
       │
       ├──► Emit user message event
       │    (event_emitter.py)
       │
       └──► Trigger agents
            (agent_runner.py)
                 │
                 ├──► Load context
                 │    (context_provider.py)
                 │
                 ├──► Get agent from registry
                 │    (agent_registry.py)
                 │
                 ├──► Run StoryAdvisor
                 │    (story_advisor.py)
                 │
                 └──► Emit agent message event
                      (event_emitter.py)
```

## Files Involved

- `test_agent_integration.py` - This test script
- `auth_helper.py` - Authentication helper (existing)
- `app/agents/agent_registry.py` - Agent registry
- `app/agents/story_advisor.py` - StoryAdvisor agent implementation
- `app/services/agent_runner.py` - Agent execution service
- `app/services/context_provider.py` - Context builder
- `app/api/routes/rooms.py` - Room API endpoints

## Success Criteria

Test is successful when:
- ✅ All 9 steps complete without errors
- ✅ At least 1 agent response received
- ✅ Context awareness tests pass
- ✅ All messages persisted correctly
- ✅ No errors in `results.errors` array
