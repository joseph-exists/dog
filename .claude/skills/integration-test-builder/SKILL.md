---
name: integration-test-builder
description: Create integration test scripts for the TinyFoot backend in backend/app/test_scripts/. Use when: (1) validating complex integrated functionality across multiple API endpoints, (2) testing end-to-end workflows like stories, rooms, or agents, (3) creating debug scripts to investigate issues, (4) testing functionality that has already been unit-tested atomically. These tests run in a full environment with minimal mocking.
---

# Integration Test Builder

Create integration test scripts that validate complex, integrated functionality against a running backend.

## When to Use

- Testing integrated workflows spanning multiple API endpoints
- Validating complex features after atomic unit tests pass
- Creating debug scripts to investigate production issues
- Testing story flows, room interactions, agent behaviors

## When NOT to Use

- Unit testing individual functions (use pytest in `backend/app/tests/`)
- Testing isolated API endpoints (use pytest)
- Mocking is the primary testing strategy

## Directory Structure

```
backend/app/test_scripts/
├── auth_helper.py          # Shared - copy to subdirectory if needed
├── story_things/           # Story-related tests
├── rooms/                  # Room/chat tests
├── agents/                 # Agent integration tests
├── archetype_loader/       # Data loading scripts
└── typer/                  # CLI commands (separate skill)
```

## Quick Start

1. **Choose or create subdirectory** based on feature area
2. **Copy auth_helper.py** to subdirectory (or import from parent)
3. **Use the template pattern** from references/template.py
4. **Run with**: `python <script>.py --verbose`

## Test Script Patterns

### Minimal Debug Script (~100 lines)

For quick debugging or single-endpoint validation:

```python
#!/usr/bin/env python3
"""Debug script description."""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session

BASE_URL = "http://localhost:8000/api/v1"

def main():
    s = get_authenticated_session()

    # Direct API calls with clear output
    response = s.get(f"{BASE_URL}/endpoint")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    main()
```

### Full Test Suite (~500-2000 lines)

For comprehensive feature validation:

```python
#!/usr/bin/env python3
"""
Feature E2E Test Suite

Usage:
    python test_feature.py
    python test_feature.py --verbose
    python test_feature.py --test group_name
"""
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
import requests

sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session, AuthenticationError

BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "test_results_feature.json"

test_results = {
    "test_suite": "Feature E2E Test Suite",
    "start_time": None,
    "end_time": None,
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "success_rate": "0%",
    "test_entities": {},
    "tests": []
}

test_entities = {}

class TestRunner:
    def __init__(self, session: requests.Session, verbose: bool = False):
        self.session = session
        self.verbose = verbose

    def log(self, msg: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def debug(self, msg: str):
        if self.verbose:
            self.log(f"DEBUG: {msg}")

    def test_header(self, name: str, desc: str = ""):
        print("\n" + "=" * 70)
        print(f"  {name}")
        if desc:
            print(f"  {desc}")
        print("=" * 70)

    def record_test(self, name: str, passed: bool, message: str):
        test_results["tests"].append({
            "name": name, "passed": passed, "message": message
        })
        test_results["total_tests"] += 1
        if passed:
            test_results["passed"] += 1
            print(f"  ✅ PASSED: {name}")
        else:
            test_results["failed"] += 1
            print(f"  ❌ FAILED: {name}\n     {message}")

    # Add test groups as methods...
    def test_group_one(self):
        self.test_header("Test Group 1", "Description")
        # Test implementation...

    def run_all_tests(self, test_filter: str = None):
        test_groups = {"group1": self.test_group_one}

        if test_filter and test_filter in test_groups:
            test_groups[test_filter]()
        else:
            for func in test_groups.values():
                func()

        return test_results["failed"] == 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--test", "-t", help="Run specific test group")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    try:
        session = get_authenticated_session()
        runner = TestRunner(session, verbose=args.verbose)
        success = runner.run_all_tests(test_filter=args.test)

        # Calculate and save results...
        test_results["end_time"] = datetime.now().isoformat()
        with open(RESULTS_FILE, "w") as f:
            json.dump(test_results, f, indent=2)

        sys.exit(0 if success else 1)
    except AuthenticationError as e:
        print(f"❌ Auth failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Key Components

### auth_helper.py

Every test script needs authentication. Import pattern:

```python
sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session, AuthenticationError
```

Requires `test.env` file with:
```
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=password
```

### TestRunner Class Methods

| Method | Purpose |
|--------|---------|
| `log(msg)` | Print with timestamp |
| `debug(msg)` | Print only if `--verbose` |
| `test_header(name, desc)` | Section separator |
| `record_test(name, passed, msg)` | Track pass/fail |
| `run_all_tests(filter)` | Execute test groups |

### test_results Structure

```python
test_results = {
    "test_suite": "Suite Name",
    "start_time": None,
    "end_time": None,
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "success_rate": "0%",
    "test_entities": {},  # IDs of created resources
    "tests": []           # Individual test results
}
```

## API Helper Patterns

### Create Resource
```python
def create_story(self, title: str, description: str) -> dict:
    payload = {"title": title, "description": description}
    self.debug(f"POST {BASE_URL}/stories")
    response = self.session.post(f"{BASE_URL}/stories", json=payload)
    if response.status_code != 200:
        raise Exception(f"Failed: {response.text}")
    return response.json()
```

### Validate Response
```python
def validate_response(self, response, expected_status=200):
    if response.status_code != expected_status:
        raise Exception(f"Expected {expected_status}, got {response.status_code}: {response.text}")
    return response.json()
```

## Running Tests

```bash
# Activate environment
source /home/josep/dog/backend/.venv/bin/activate
cd /home/josep/dog/backend/app/test_scripts/<area>

# Run all tests
python test_feature.py

# Verbose output
python test_feature.py --verbose

# Specific test group
python test_feature.py --test group_name
```

## Reference Examples

| File | Type | Lines | Use Case |
|------|------|-------|----------|
| `story_things/test_branching_story_state.py` | Full suite | ~1800 | Comprehensive feature testing |
| `story_things/test-story-zed.py` | Minimal | ~500 | Quick validation script |
| `story_things/debug_validate_state.py` | Debug | ~100 | Single endpoint investigation |

## Output

- Console: Pass/fail with emoji indicators
- JSON file: `test_results_<feature>.json` for CI/parsing
- Exit code: 0 success, 1 failure
