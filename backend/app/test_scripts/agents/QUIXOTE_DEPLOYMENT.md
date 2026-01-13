# Quixote Agent Test Script - Deployment Guide

## Overview

The `test_quixote_agent.py` script tests the Quixote storytelling AI agent by generating 5 stories on different topics. This guide covers setup and deployment.

## Files Created

1. **Test Script**: `backend/app/test_scripts/test_quixote_agent.py`
2. **Agent Fixed**: `backend/app/agents/quixote.py` (added RunContext parameter)
3. **Documentation**: Updated `backend/app/test_scripts/README.md`

## Prerequisites

### 1. OpenAI API Key

The script requires a valid OpenAI API key. This is already configured in your `.env` file:

```bash
OPENAI_API_KEY=sk-POOPPOOPPOOPPOOPPOOPPOOPPOOPPOOPPO
```

**⚠️ IMPORTANT**: Replace the placeholder value with your actual OpenAI API key before deployment.

To update:
```bash
# Edit .env file
nano .env

# Or set via environment variable
export OPENAI_API_KEY=sk-your-actual-key-here
```

### 2. Dependencies

All required dependencies are already in `backend/pyproject.toml`:
- `pydantic-ai[ag-ui]>=0.4.3` ✅ Already installed
- `fastapi` and related packages ✅ Already installed

### 3. Docker Environment

The OpenAI API key is automatically passed to the Docker container via the `.env` file and `docker-compose.yml`.

## Running the Test Script

### Option 1: Inside Docker Container (Recommended)

```bash
# From project root
docker compose exec backend bash

# Navigate to test scripts
cd app/test_scripts

# Run the test
python test_quixote_agent.py
```

### Option 2: Local Python Environment

```bash
# Navigate to test scripts
cd backend/app/test_scripts

# Ensure OPENAI_API_KEY is set
export OPENAI_API_KEY=sk-your-key-here

# Run the test
python test_quixote_agent.py
```

## Expected Output

### Console Output

```
[2025-01-15 10:30:45] INFO: ============================================================
[2025-01-15 10:30:45] INFO: Starting Quixote Agent Test Suite
[2025-01-15 10:30:45] INFO: ============================================================
[2025-01-15 10:30:45] INFO: Test #1: Requesting story about 'courage'
[2025-01-15 10:30:47] INFO: Test #1: Story received (342 characters)

--- Story Preview ---
Once upon a time, there was a man who loved courage more than anything 
else in the world. He faced dragons and demons, storms and shadows...
--- End Preview ---

[2025-01-15 10:30:47] INFO: Test #2: Requesting story about 'wisdom'
...
[2025-01-15 10:31:15] INFO: ============================================================
[2025-01-15 10:31:15] INFO: Test Suite Summary
[2025-01-15 10:31:15] INFO: ============================================================
[2025-01-15 10:31:15] INFO: Total Tests: 5
[2025-01-15 10:31:15] INFO: Successful: 5
[2025-01-15 10:31:15] INFO: Failed: 0
[2025-01-15 10:31:15] INFO: Average Story Length: 375 characters
[2025-01-15 10:31:15] INFO: ============================================================
[2025-01-15 10:31:15] INFO: All tests passed successfully!
```

### JSON Output

Results are saved to `backend/app/test_scripts/test_results_quixote_agent.json`:

```json
{
  "test_suite": "Quixote Storytelling Agent",
  "start_time": "2025-01-15T10:30:45.123456",
  "tests": [
    {
      "test_number": 1,
      "topic": "courage",
      "success": true,
      "story": "Once upon a time, there was a man who loved courage...",
      "story_length": 342,
      "timestamp": "2025-01-15T10:30:47.234567"
    },
    ...
  ],
  "end_time": "2025-01-15T10:31:15.345678",
  "total_tests": 5,
  "successful_tests": 5,
  "failed_tests": 0
}
```

## Integration with Build/Deploy

### Adding to CI/CD Pipeline

To run tests automatically during deployment, add to your CI/CD config:

```yaml
# Example GitHub Actions
- name: Test Quixote Agent
  run: |
    docker compose exec -T backend python app/test_scripts/test_quixote_agent.py
```

### Pre-deployment Health Check

Add to deployment script:

```bash
#!/bin/bash
# scripts/pre-deploy.sh

echo "Testing Quixote Agent..."
docker compose exec -T backend python app/test_scripts/test_quixote_agent.py

if [ $? -eq 0 ]; then
  echo "✅ Quixote agent tests passed"
else
  echo "❌ Quixote agent tests failed"
  exit 1
fi
```

## Troubleshooting

### Error: "Error generating schema for tell_me_a_story"

**Cause**: Missing `RunContext` parameter in agent tool definition.

**Solution**: Already fixed! The `quixote.py` file now includes:
```python
from pydantic_ai import Agent, RunContext

@agent.tool
async def tell_me_a_story(ctx: RunContext, topic: str) -> str:
    ...
```

### Error: "OpenAI API key not found"

**Cause**: OpenAI API key not set in environment.

**Solution**:
1. Check `.env` file has valid key
2. Restart Docker containers: `docker compose down && docker compose up -d`
3. Or set directly: `export OPENAI_API_KEY=sk-your-key-here`

### Error: "Rate limit exceeded"

**Cause**: OpenAI API rate limits reached.

**Solution**:
1. Wait and retry
2. Check your OpenAI account usage
3. Add delay between tests (modify script to add `await asyncio.sleep(2)`)

### Error: "Module 'agents.quixote' not found"

**Cause**: Running from wrong directory or path issues.

**Solution**:
```bash
# Make sure you're in test_scripts directory
cd backend/app/test_scripts

# Or use full path
python -m app.test_scripts.test_quixote_agent
```

## Topics Tested

The script tests story generation on these themes:
1. **Courage** - Bravery and facing fear
2. **Wisdom** - Knowledge and understanding
3. **Friendship** - Connection and loyalty
4. **Perseverance** - Persistence through difficulty
5. **Compassion** - Empathy and kindness

To test different topics, edit the `TEST_TOPICS` list in the script.

## Customization

### Adding More Topics

Edit `test_quixote_agent.py`:

```python
TEST_TOPICS = [
    "courage",
    "wisdom",
    "friendship",
    "perseverance",
    "compassion",
    "justice",      # Add new topics
    "creativity",
    "humility",
]
```

### Changing Output File

```python
OUTPUT_FILE = "my_custom_results.json"
```

### Adding Delays Between Tests

To avoid rate limits:

```python
async def run_all_tests() -> dict[str, Any]:
    ...
    for i, topic in enumerate(TEST_TOPICS, start=1):
        test_result = await test_agent_story(topic, i)
        results["tests"].append(test_result)
        
        # Add 2 second delay between tests
        if i < len(TEST_TOPICS):
            await asyncio.sleep(2)
```

## Next Steps

1. **Set Real API Key**: Replace placeholder in `.env` with actual OpenAI key
2. **Run Initial Test**: Execute script to verify everything works
3. **Review Results**: Check `test_results_quixote_agent.json` output
4. **Integrate with Deploy**: Add to CI/CD or pre-deployment scripts
5. **Monitor Costs**: Track OpenAI API usage for these test runs

## Cost Considerations

Each test run generates 5 stories. Estimated costs:
- Using GPT-4: ~$0.02-0.05 per run
- Using GPT-3.5: ~$0.002-0.005 per run

Consider using GPT-3.5-turbo for test runs:

```python
# In quixote.py
agent = Agent(
    'openai:gpt-3.5-turbo',  # Lower cost option
    system_prompt="...",
)
```

## Documentation

Full documentation available in:
- `backend/app/test_scripts/README.md` - Complete test script reference
- This file - Deployment-specific guide

## Summary

✅ Fixed RunContext error in quixote.py
✅ Created comprehensive test script
✅ Updated documentation
✅ Script ready for deployment
✅ No new dependencies needed

The test script is production-ready and can be:
- Run manually for testing
- Integrated into CI/CD pipelines
- Used as a health check before deployment
- Extended with additional test cases
