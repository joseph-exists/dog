# Quixote Agent Test Script - Quick Reference

## What Changed

The test script now uses the correct pydantic-ai API:

### ✅ Correct API Usage

```python
# Run the agent
result = await agent.run(f"Tell me a story about {topic}")

# Access the story
story = result.output  # ✅ CORRECT

# Get token usage
usage = result.usage()
print(f"Tokens: {usage.total_tokens}")

# Get timestamp
timestamp = result.timestamp()

# Get run ID
run_id = result.run_id
```

### ❌ Old (Incorrect) API

```python
story = result.data  # ❌ WRONG - AttributeError
```

## New Features

The updated script now tracks:

1. **Token Usage** - Request, response, and total tokens for each story
2. **Run IDs** - Unique identifier for each agent run
3. **Timestamps** - Precise timing from the agent itself
4. **Usage Summary** - Aggregate token statistics across all tests

## Sample Output

```bash
[2025-12-11 21:30:45] INFO: Test #1: Requesting story about 'courage'
[2025-12-11 21:30:47] INFO: Test #1: Story received (342 characters)
[2025-12-11 21:30:47] INFO: Test #1: Tokens - Request: 45, Response: 298, Total: 343

--- Story Preview ---
Once upon a time, there was a man who loved courage more than anything 
else in the world. He faced dragons and demons, storms and shadows...
--- End Preview ---

...

[2025-12-11 21:31:15] INFO: Test Suite Summary
[2025-12-11 21:31:15] INFO: Total Tests: 5
[2025-12-11 21:31:15] INFO: Successful: 5
[2025-12-11 21:31:15] INFO: Failed: 0
[2025-12-11 21:31:15] INFO: Average Story Length: 375 characters
[2025-12-11 21:31:15] INFO: Total Tokens Used: 1685
[2025-12-11 21:31:15] INFO:   - Request Tokens: 225
[2025-12-11 21:31:15] INFO:   - Response Tokens: 1460
[2025-12-11 21:31:15] INFO: Average Tokens per Story: 337
```

## JSON Output Format

```json
{
  "test_suite": "Quixote Storytelling Agent",
  "start_time": "2025-12-11T21:30:45.123456",
  "tests": [
    {
      "test_number": 1,
      "topic": "courage",
      "success": true,
      "story": "Once upon a time...",
      "story_length": 342,
      "usage": {
        "request_tokens": 45,
        "response_tokens": 298,
        "total_tokens": 343
      },
      "run_id": "unique-run-id-here",
      "timestamp": "2025-12-11T21:30:47.234567"
    }
  ],
  "end_time": "2025-12-11T21:31:15.345678",
  "total_tests": 5,
  "successful_tests": 5,
  "failed_tests": 0,
  "token_usage_summary": {
    "total_tokens": 1685,
    "total_request_tokens": 225,
    "total_response_tokens": 1460,
    "average_tokens_per_story": 337.0
  },
  "average_story_length": 375.0
}
```

## Running the Script

```bash
# Inside Docker
docker compose exec backend bash
cd app/test_scripts
python test_quixote_agent.py

# Exit code: 0 = success, 1 = failure
```

## Common pydantic-ai Attributes

When working with `AgentRunResult`:

- `result.output` - The validated output from the agent ✅
- `result.usage()` - Token usage information ✅
- `result.timestamp()` - When the response was generated ✅
- `result.run_id` - Unique identifier for this run ✅
- `result.all_messages()` - Complete message history
- `result.new_messages()` - Only new messages from this run

## Cost Tracking

The script now provides detailed token usage, making it easy to:

- Estimate API costs before running at scale
- Compare token efficiency across different topics
- Track total token consumption per test run

Example calculation for GPT-4:
- Input: $0.03 per 1K tokens
- Output: $0.06 per 1K tokens
- 225 request tokens: ~$0.007
- 1460 response tokens: ~$0.088
- **Total per run: ~$0.095**

## Files Updated

1. ✅ `test_quixote_agent.py` - Rewritten with correct API
2. ✅ `quixote.py` - Fixed RunContext parameter
3. ✅ `README.md` - Updated with documentation
4. ✅ This quick reference - API usage guide

## Ready to Deploy

The script is now production-ready with:
- ✅ Correct pydantic-ai API usage
- ✅ Comprehensive token tracking
- ✅ Error handling and recovery
- ✅ Detailed logging and reporting
- ✅ JSON output for analysis
- ✅ Exit codes for CI/CD integration
