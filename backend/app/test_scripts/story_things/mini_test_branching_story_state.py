#!/usr/bin/env python3
"""
Story State Schema E2E Test Suite (Minimal)

Tests the StoryStateSchema functionality:
- StoryStateVariable CRUD operations
- Value types (boolean, number, string, enum)
- Validation of undefined variables in choices
- Soft block on publish with undefined variables

Usage:
    python test_branching_story_state.py
    python test_branching_story_state.py --verbose

Output:
    mini_test_results_story_state.json
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

import requests

# Import auth helper
sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session, AuthenticationError


# Configuration
BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "mini_test_results_story_state.json"

# Test state
test_results = {
    "test_suite": "Story State Schema E2E Test Suite",
    "start_time": None,
    "end_time": None,
    "duration_seconds": 0,
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "success_rate": "0%",
    "tests": []
}

test_entities = {}  # Stores created entity IDs


class TestRunner:
    """Runs story state schema tests."""

    def __init__(self, session: requests.Session, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.user = None

    def log(self, message: str):
        """Print message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def debug(self, message: str):
        """Print debug message if verbose."""
        if self.verbose:
            self.log(f"DEBUG: {message}")

    def test_header(self, test_name: str, description: str = ""):
        """Print test header."""
        print("\n" + "=" * 70)
        print(f"  {test_name}")
        if description:
            print(f"  {description}")
        print("=" * 70)

    def record_test(self, name: str, passed: bool, message: str, details: dict = None):
        """Record test result."""
        test_results["tests"].append({
            "name": name,
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
        test_results["total_tests"] += 1
        if passed:
            test_results["passed"] += 1
            print(f"  ✅ PASSED: {name}")
            if message:
                print(f"     {message}")
        else:
            test_results["failed"] += 1
            print(f"  ❌ FAILED: {name}")
            print(f"     {message}")

    def authenticate(self):
        """Authenticate and get user info."""
        response = self.session.get(f"{BASE_URL}/users/me")

        if response.status_code == 200:
            user_data = response.json()
            self.user = user_data
            print(f"  ✅ Authenticated as: {user_data.get('email')}")
        else:
            raise Exception("Failed to get user info")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def create_story(self, title: str, description: str) -> dict:
        """Create a story and return its data."""
        story_data = {
            "title": title,
            "description": description,
            "current_version": 1
        }

        self.debug(f"Creating story: {title}")
        response = self.session.post(f"{BASE_URL}/stories", json=story_data)

        if response.status_code != 200:
            raise Exception(f"Failed to create story: {response.text}")

        story = response.json()
        self.debug(f"Story created: {story['id'][:8]}...")
        return story

    def create_node(self, story_id: str, title: str, content: str,
                   is_start: bool = False, is_end: bool = False) -> dict:
        """Create a story node."""
        self.debug(f"Creating node: {title}")
        response = self.session.post(
            f"{BASE_URL}/storynodes",
            json={
                "story_id": story_id,
                "story_version": 1,
                "title": title,
                "content": content,
                "node_type": "text",
                "content_format": "text",
                "is_start_node": is_start,
                "is_end_node": is_end
            }
        )
        if response.status_code != 200:
            raise Exception(f"Failed to create node {title}: {response.text}")
        return response.json()

    def create_choice(self, from_node_id: str, to_node_id: str, text: str,
                     sets_state: dict = None, requires_state: dict = None,
                     order: int = 0) -> dict:
        """Create a choice between nodes."""
        self.debug(f"Creating choice: {text}")
        payload = {
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "text": text,
            "order": order
        }
        if sets_state:
            payload["sets_state"] = sets_state
        if requires_state:
            payload["requires_state"] = requires_state

        response = self.session.post(f"{BASE_URL}/node-choices", json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to create choice '{text}': {response.text}")
        return response.json()

    # ========================================================================
    # State Schema API Methods
    # ========================================================================

    def get_state_schema(self, story_id: str, version: int = 1) -> dict:
        """Get state schema variables for a story version."""
        self.debug(f"Getting state schema for story {story_id[:8]}... v{version}")
        response = self.session.get(
            f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to get state schema: {response.text}")
        return response.json()

    def create_state_variable(self, story_id: str, version: int,
                             key: str, value_type: str,
                             default_value=None, enum_values: list = None,
                             description: str = None, category: str = None) -> dict:
        """Create a state variable in the schema."""
        self.debug(f"Creating state variable: {key} ({value_type})")
        payload = {
            "key": key,
            "value_type": value_type,
        }
        if default_value is not None:
            payload["default_value"] = default_value
        if enum_values:
            payload["enum_values"] = enum_values
        if description:
            payload["description"] = description
        if category:
            payload["category"] = category

        response = self.session.post(
            f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema",
            json=payload
        )
        if response.status_code != 200:
            raise Exception(f"Failed to create state variable: {response.text}")
        return response.json()

    def update_state_variable(self, story_id: str, version: int,
                             variable_id: str, **kwargs) -> dict:
        """Update a state variable."""
        self.debug(f"Updating state variable: {variable_id[:8]}...")
        response = self.session.put(
            f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema/{variable_id}",
            json=kwargs
        )
        if response.status_code != 200:
            raise Exception(f"Failed to update state variable: {response.text}")
        return response.json()

    def delete_state_variable(self, story_id: str, version: int,
                             variable_id: str) -> bool:
        """Delete a state variable."""
        self.debug(f"Deleting state variable: {variable_id[:8]}...")
        response = self.session.delete(
            f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema/{variable_id}"
        )
        return response.status_code in [200, 204]

    def validate_state_schema(self, story_id: str, version: int = 1) -> dict:
        """Validate state schema against choices."""
        self.debug(f"Validating state schema for story {story_id[:8]}...")
        response = self.session.get(
            f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema/validate"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to validate state schema: {response.text}")
        return response.json()

    # ========================================================================
    # Test: Basic CRUD Operations
    # ========================================================================

    def test_state_variable_crud(self):
        """Test basic CRUD operations for state variables."""
        self.test_header(
            "Test 1: State Variable CRUD",
            "Create, read, update, delete state variables"
        )

        try:
            # Create a test story
            story = self.create_story(
                "State Schema Test Story",
                "Testing state variable CRUD operations"
            )
            story_id = story["id"]
            test_entities["story_id"] = story_id

            # CREATE - Test different value types
            self.log("Testing CREATE operations...")

            # Boolean variable
            bool_var = self.create_state_variable(
                story_id, 1,
                key="has_key",
                value_type="boolean",
                default_value=False,
                description="Whether player has the key",
                category="inventory"
            )
            self.debug(f"Created boolean var: {bool_var['id'][:8]}...")

            # Number variable
            num_var = self.create_state_variable(
                story_id, 1,
                key="courage",
                value_type="number",
                default_value=0,
                description="Player's courage level",
                category="stats"
            )
            self.debug(f"Created number var: {num_var['id'][:8]}...")

            # String variable
            str_var = self.create_state_variable(
                story_id, 1,
                key="player_name",
                value_type="string",
                default_value="Adventurer",
                description="Player's chosen name"
            )
            self.debug(f"Created string var: {str_var['id'][:8]}...")

            # Enum variable
            enum_var = self.create_state_variable(
                story_id, 1,
                key="faction",
                value_type="enum",
                enum_values=["rebel", "empire", "neutral"],
                default_value="neutral",
                description="Player's faction alignment",
                category="alignment"
            )
            self.debug(f"Created enum var: {enum_var['id'][:8]}...")

            # READ - Get all variables
            self.log("Testing READ operations...")
            schema = self.get_state_schema(story_id, 1)

            if schema.get("count", 0) != 4:
                raise Exception(f"Expected 4 variables, got {schema.get('count', 0)}")

            var_keys = [v["key"] for v in schema.get("data", [])]
            expected_keys = ["has_key", "courage", "player_name", "faction"]
            for key in expected_keys:
                if key not in var_keys:
                    raise Exception(f"Missing variable: {key}")

            self.record_test(
                "create_state_variables",
                True,
                f"Created 4 variables (boolean, number, string, enum)"
            )

            # UPDATE - Modify a variable
            self.log("Testing UPDATE operations...")
            updated_var = self.update_state_variable(
                story_id, 1, bool_var["id"],
                description="Whether player has found the golden key",
                default_value=True
            )

            if updated_var.get("description") != "Whether player has found the golden key":
                raise Exception("Update did not change description")
            if updated_var.get("default_value") != True:
                raise Exception("Update did not change default_value")

            self.record_test(
                "update_state_variable",
                True,
                f"Updated variable description and default_value"
            )

            # DELETE - Remove a variable
            self.log("Testing DELETE operations...")
            if not self.delete_state_variable(story_id, 1, str_var["id"]):
                raise Exception("Delete operation failed")

            # Verify deletion
            schema_after = self.get_state_schema(story_id, 1)
            if schema_after.get("count", 0) != 3:
                raise Exception(f"Expected 3 variables after delete, got {schema_after.get('count', 0)}")

            self.record_test(
                "delete_state_variable",
                True,
                f"Deleted variable, count now {schema_after.get('count', 0)}"
            )

        except Exception as e:
            self.record_test(
                "state_variable_crud",
                False,
                str(e)
            )

    # ========================================================================
    # Test: Validation of Undefined Variables
    # ========================================================================

    def test_undefined_variable_validation(self):
        """Test validation detects undefined variables in choices."""
        self.test_header(
            "Test 2: Undefined Variable Validation",
            "Verify validation catches undefined state variables"
        )

        try:
            # Create a test story
            story = self.create_story(
                "Validation Test Story",
                "Testing undefined variable detection"
            )
            story_id = story["id"]

            # Define only some variables in schema
            self.create_state_variable(
                story_id, 1,
                key="defined_var",
                value_type="boolean",
                default_value=False
            )

            # Create nodes
            start_node = self.create_node(
                story_id, "Start", "The beginning...", is_start=True
            )
            end_node = self.create_node(
                story_id, "End", "The end.", is_end=True
            )

            # Create choice with UNDEFINED variables
            self.create_choice(
                start_node["id"], end_node["id"],
                "Make a choice",
                sets_state={
                    "defined_var": True,
                    "undefined_var_1": "oops",  # NOT in schema
                    "undefined_var_2": 42       # NOT in schema
                },
                requires_state={
                    "another_undefined": True   # NOT in schema
                }
            )

            # Validate - should report undefined variables
            validation = self.validate_state_schema(story_id, 1)

            self.debug(f"Validation result: {json.dumps(validation, indent=2)}")

            if validation.get("is_valid", True):
                raise Exception("Validation should have failed with undefined variables")

            undefined = validation.get("undefined_variables", [])
            if len(undefined) < 3:
                raise Exception(f"Expected at least 3 undefined vars, got {len(undefined)}")

            # Check specific undefined vars are reported
            expected_undefined = ["undefined_var_1", "undefined_var_2", "another_undefined"]
            for var in expected_undefined:
                if var not in undefined:
                    raise Exception(f"Missing undefined variable in report: {var}")

            self.record_test(
                "detect_undefined_variables",
                True,
                f"Detected {len(undefined)} undefined variables: {', '.join(undefined)}"
            )

            # Verify defined variable is recognized
            defined = validation.get("defined_variables", [])
            if "defined_var" not in defined:
                raise Exception("defined_var should be in defined_variables list")

            self.record_test(
                "recognize_defined_variables",
                True,
                f"Correctly recognized defined variable: defined_var"
            )

        except Exception as e:
            self.record_test(
                "undefined_variable_validation",
                False,
                str(e)
            )

    # ========================================================================
    # Test: Valid Schema (No Errors)
    # ========================================================================

    def test_valid_schema(self):
        """Test validation passes when all variables are defined."""
        self.test_header(
            "Test 3: Valid Schema Validation",
            "Verify validation passes with fully defined schema"
        )

        try:
            # Create a test story
            story = self.create_story(
                "Valid Schema Test",
                "Testing validation with complete schema"
            )
            story_id = story["id"]

            # Define ALL variables that will be used
            self.create_state_variable(
                story_id, 1,
                key="path",
                value_type="string"
            )
            self.create_state_variable(
                story_id, 1,
                key="courage",
                value_type="number",
                default_value=0
            )
            self.create_state_variable(
                story_id, 1,
                key="has_sword",
                value_type="boolean",
                default_value=False
            )

            # Create nodes
            start = self.create_node(story_id, "Start", "Begin...", is_start=True)
            middle = self.create_node(story_id, "Middle", "Continue...")
            end = self.create_node(story_id, "End", "Finish.", is_end=True)

            # Create choices using ONLY defined variables
            self.create_choice(
                start["id"], middle["id"],
                "Take the brave path",
                sets_state={"path": "brave", "courage": 10}
            )
            self.create_choice(
                middle["id"], end["id"],
                "Draw the sword",
                requires_state={"courage": 10},
                sets_state={"has_sword": True}
            )

            # Validate - should pass
            validation = self.validate_state_schema(story_id, 1)

            if not validation.get("is_valid", False):
                errors = validation.get("errors", [])
                raise Exception(f"Validation should have passed, but got errors: {errors}")

            undefined = validation.get("undefined_variables", [])
            if len(undefined) > 0:
                raise Exception(f"Should have no undefined variables, got: {undefined}")

            self.record_test(
                "valid_schema_passes",
                True,
                "Validation passed with 0 undefined variables"
            )

        except Exception as e:
            self.record_test(
                "valid_schema",
                False,
                str(e)
            )

    # ========================================================================
    # Main Test Runner
    # ========================================================================

    def run_all_tests(self):
        """Run all state schema tests."""
        self.test_header(
            "STORY STATE SCHEMA E2E TEST SUITE",
            "Testing StoryStateVariable CRUD and validation"
        )

        try:
            # Authenticate
            self.authenticate()

            # Run tests
            self.test_state_variable_crud()
            self.test_undefined_variable_validation()
            self.test_valid_schema()

        except Exception as e:
            self.log(f"Fatal error: {e}")
            return False

        return test_results["failed"] == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="E2E tests for Story State Schema"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  STORY STATE SCHEMA E2E TEST SUITE")
    print("  Testing StoryStateVariable CRUD and validation")
    print("=" * 70)

    try:
        # Get authenticated session
        session = get_authenticated_session()

        # Create test runner
        runner = TestRunner(session, verbose=args.verbose)

        # Run tests
        success = runner.run_all_tests()

        # Calculate results
        test_results["end_time"] = datetime.now().isoformat()
        start = datetime.fromisoformat(test_results["start_time"])
        end = datetime.fromisoformat(test_results["end_time"])
        test_results["duration_seconds"] = (end - start).total_seconds()

        if test_results["total_tests"] > 0:
            rate = (test_results["passed"] / test_results["total_tests"]) * 100
            test_results["success_rate"] = f"{rate:.1f}%"

        # Write results
        with open(RESULTS_FILE, "w") as f:
            json.dump(test_results, f, indent=2)

        # Summary
        print("\n" + "=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70)
        print(f"  Total Tests:     {test_results['total_tests']}")
        print(f"  ✅ Passed:        {test_results['passed']}")
        print(f"  ❌ Failed:        {test_results['failed']}")
        print(f"  Success Rate:    {test_results['success_rate']}")
        print(f"  Duration:        {test_results['duration_seconds']:.2f}s")
        print(f"\n  Results saved to: {RESULTS_FILE}")
        print("=" * 70 + "\n")

        sys.exit(0 if success else 1)

    except AuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("Check test.env file and credentials")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
