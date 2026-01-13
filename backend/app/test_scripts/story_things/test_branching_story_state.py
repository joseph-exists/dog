#!/usr/bin/env python3
"""
Story State Schema E2E Test Suite

Comprehensive tests for the StoryStateSchema functionality:
- StoryStateVariable CRUD operations (all value types)
- Value type validation and constraints
- Enum validation (requires enum_values)
- Undefined variable detection in choices
- Complex multi-choice validation scenarios
- Publish integration (soft block on undefined vars)
- Edge cases and error handling
- Category organization

Usage:
    python test_branching_story_state.py
    python test_branching_story_state.py --verbose
    python test_branching_story_state.py --test crud
    python test_branching_story_state.py --test validation
    python test_branching_story_state.py --test publish

Output:
    test_results_story_state.json
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
RESULTS_FILE = "test_results_story_state.json"

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
    "test_entities": {},
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

    def subtest_header(self, test_name: str):
        """Print subtest header."""
        print(f"\n  --- {test_name} ---")

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
    # Helper Methods - Story/Node/Choice Creation
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

    def publish_story(self, story_id: str) -> tuple[bool, dict]:
        """Attempt to publish a story. Returns (success, response_data)."""
        self.debug(f"Publishing story {story_id[:8]}...")
        response = self.session.put(f"{BASE_URL}/stories/{story_id}/publish")
        return response.status_code == 200, response.json() if response.text else {}

    # ========================================================================
    # Helper Methods - State Schema API
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
                             description: str = None, category: str = None,
                             expect_failure: bool = False) -> dict | None:
        """Create a state variable in the schema."""
        self.debug(f"Creating state variable: {key} ({value_type})")
        payload = {
            "key": key,
            "value_type": value_type,
        }
        if default_value is not None:
            payload["default_value"] = default_value
        if enum_values is not None:
            payload["enum_values"] = enum_values
        if description:
            payload["description"] = description
        if category:
            payload["category"] = category

        response = self.session.post(
            f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema",
            json=payload
        )

        if expect_failure:
            if response.status_code == 200:
                raise Exception(f"Expected failure but got success for: {key}")
            return None

        if response.status_code != 200:
            raise Exception(f"Failed to create state variable: {response.text}")
        return response.json()

    def create_state_variable_raw(self, story_id: str, version: int, payload: dict) -> requests.Response:
        """Create a state variable and return raw response (for error testing)."""
        return self.session.post(
            f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema",
            json=payload
        )

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
    # TEST GROUP 1: Basic CRUD Operations
    # ========================================================================

    def test_state_variable_crud(self):
        """Test basic CRUD operations for state variables."""
        self.test_header(
            "Test Group 1: State Variable CRUD",
            "Create, read, update, delete state variables"
        )

        try:
            # Create a test story
            story = self.create_story(
                "State Schema CRUD Test",
                "Testing state variable CRUD operations"
            )
            story_id = story["id"]
            test_entities["crud_story_id"] = story_id

            # ----------------------------------------------------------------
            # TEST 1.1: Create Boolean Variable
            # ----------------------------------------------------------------
            self.subtest_header("1.1 Create Boolean Variable")

            bool_var = self.create_state_variable(
                story_id, 1,
                key="has_key",
                value_type="boolean",
                default_value=False,
                description="Whether player has the key",
                category="inventory"
            )

            if bool_var["key"] != "has_key":
                raise Exception("Key mismatch")
            if bool_var["value_type"] != "boolean":
                raise Exception("Value type mismatch")
            if bool_var["default_value"] != False:
                raise Exception("Default value mismatch")
            if bool_var["category"] != "inventory":
                raise Exception("Category mismatch")

            self.record_test(
                "create_boolean_variable",
                True,
                f"Created boolean var with default=False, category=inventory"
            )

            # ----------------------------------------------------------------
            # TEST 1.2: Create Number Variable
            # ----------------------------------------------------------------
            self.subtest_header("1.2 Create Number Variable")

            num_var = self.create_state_variable(
                story_id, 1,
                key="courage",
                value_type="number",
                default_value=0,
                description="Player's courage level (0-100)",
                category="stats"
            )

            if num_var["value_type"] != "number":
                raise Exception("Value type mismatch")
            if num_var["default_value"] != 0:
                raise Exception("Default value mismatch")

            self.record_test(
                "create_number_variable",
                True,
                f"Created number var with default=0"
            )

            # ----------------------------------------------------------------
            # TEST 1.3: Create String Variable
            # ----------------------------------------------------------------
            self.subtest_header("1.3 Create String Variable")

            str_var = self.create_state_variable(
                story_id, 1,
                key="player_name",
                value_type="string",
                default_value="Adventurer",
                description="Player's chosen name"
            )

            if str_var["value_type"] != "string":
                raise Exception("Value type mismatch")
            if str_var["default_value"] != "Adventurer":
                raise Exception("Default value mismatch")

            self.record_test(
                "create_string_variable",
                True,
                f"Created string var with default='Adventurer'"
            )

            # ----------------------------------------------------------------
            # TEST 1.4: Create Enum Variable
            # ----------------------------------------------------------------
            self.subtest_header("1.4 Create Enum Variable")

            enum_var = self.create_state_variable(
                story_id, 1,
                key="faction",
                value_type="enum",
                enum_values=["rebel", "empire", "neutral"],
                default_value="neutral",
                description="Player's faction alignment",
                category="alignment"
            )

            if enum_var["value_type"] != "enum":
                raise Exception("Value type mismatch")
            if enum_var["enum_values"] != ["rebel", "empire", "neutral"]:
                raise Exception("Enum values mismatch")
            if enum_var["default_value"] != "neutral":
                raise Exception("Default value mismatch")

            self.record_test(
                "create_enum_variable",
                True,
                f"Created enum var with values=['rebel', 'empire', 'neutral']"
            )

            # ----------------------------------------------------------------
            # TEST 1.5: Read All Variables
            # ----------------------------------------------------------------
            self.subtest_header("1.5 Read All Variables")

            schema = self.get_state_schema(story_id, 1)

            if schema.get("count", 0) != 4:
                raise Exception(f"Expected 4 variables, got {schema.get('count', 0)}")

            var_keys = {v["key"] for v in schema.get("data", [])}
            expected_keys = {"has_key", "courage", "player_name", "faction"}
            if var_keys != expected_keys:
                raise Exception(f"Key mismatch: {var_keys} != {expected_keys}")

            self.record_test(
                "read_all_variables",
                True,
                f"Retrieved all 4 variables successfully"
            )

            # ----------------------------------------------------------------
            # TEST 1.6: Update Variable Description
            # ----------------------------------------------------------------
            self.subtest_header("1.6 Update Variable Description")

            updated_var = self.update_state_variable(
                story_id, 1, bool_var["id"],
                description="Whether player has found the golden key"
            )

            if updated_var["description"] != "Whether player has found the golden key":
                raise Exception("Description not updated")
            if updated_var["key"] != "has_key":
                raise Exception("Key changed unexpectedly")

            self.record_test(
                "update_variable_description",
                True,
                f"Updated description successfully"
            )

            # ----------------------------------------------------------------
            # TEST 1.7: Update Variable Default Value
            # ----------------------------------------------------------------
            self.subtest_header("1.7 Update Variable Default Value")

            updated_var = self.update_state_variable(
                story_id, 1, num_var["id"],
                default_value=50
            )

            if updated_var["default_value"] != 50:
                raise Exception("Default value not updated")

            self.record_test(
                "update_variable_default",
                True,
                f"Updated default_value from 0 to 50"
            )

            # ----------------------------------------------------------------
            # TEST 1.8: Update Enum Values
            # ----------------------------------------------------------------
            self.subtest_header("1.8 Update Enum Values")

            updated_enum = self.update_state_variable(
                story_id, 1, enum_var["id"],
                enum_values=["rebel", "empire", "neutral", "independent"]
            )

            if "independent" not in updated_enum["enum_values"]:
                raise Exception("New enum value not added")
            if len(updated_enum["enum_values"]) != 4:
                raise Exception("Enum values count mismatch")

            self.record_test(
                "update_enum_values",
                True,
                f"Added 'independent' to enum values"
            )

            # ----------------------------------------------------------------
            # TEST 1.9: Delete Variable
            # ----------------------------------------------------------------
            self.subtest_header("1.9 Delete Variable")

            if not self.delete_state_variable(story_id, 1, str_var["id"]):
                raise Exception("Delete operation failed")

            schema_after = self.get_state_schema(story_id, 1)
            if schema_after.get("count", 0) != 3:
                raise Exception(f"Expected 3 variables after delete, got {schema_after.get('count', 0)}")

            remaining_keys = {v["key"] for v in schema_after.get("data", [])}
            if "player_name" in remaining_keys:
                raise Exception("Deleted variable still present")

            self.record_test(
                "delete_variable",
                True,
                f"Deleted variable, count now 3"
            )

            # ----------------------------------------------------------------
            # TEST 1.10: Create Variable Without Optional Fields
            # ----------------------------------------------------------------
            self.subtest_header("1.10 Create Variable Without Optional Fields")

            minimal_var = self.create_state_variable(
                story_id, 1,
                key="simple_flag",
                value_type="boolean"
            )

            if minimal_var["key"] != "simple_flag":
                raise Exception("Key mismatch")
            if minimal_var.get("description") is not None and minimal_var.get("description") != "":
                # Allow None or empty string
                if minimal_var.get("description"):
                    raise Exception(f"Description should be empty, got: {minimal_var.get('description')}")
            if minimal_var.get("category") is not None and minimal_var.get("category") != "":
                if minimal_var.get("category"):
                    raise Exception(f"Category should be empty, got: {minimal_var.get('category')}")

            self.record_test(
                "create_minimal_variable",
                True,
                f"Created variable with only required fields"
            )

        except Exception as e:
            self.record_test(
                "state_variable_crud",
                False,
                str(e)
            )

    # ========================================================================
    # TEST GROUP 2: Value Type Validation
    # ========================================================================

    def test_value_type_validation(self):
        """Test value type constraints and validation."""
        self.test_header(
            "Test Group 2: Value Type Validation",
            "Enum requires enum_values, type constraints"
        )

        try:
            story = self.create_story(
                "Value Type Validation Test",
                "Testing value type constraints"
            )
            story_id = story["id"]
            test_entities["validation_story_id"] = story_id

            # ----------------------------------------------------------------
            # TEST 2.1: Enum Without enum_values Should Fail
            # ----------------------------------------------------------------
            self.subtest_header("2.1 Enum Without enum_values")

            response = self.create_state_variable_raw(
                story_id, 1,
                {"key": "bad_enum", "value_type": "enum"}
            )

            if response.status_code == 200:
                self.record_test(
                    "enum_requires_values",
                    False,
                    "Should have rejected enum without enum_values"
                )
            else:
                self.record_test(
                    "enum_requires_values",
                    True,
                    f"Correctly rejected enum without enum_values (status {response.status_code})"
                )

            # ----------------------------------------------------------------
            # TEST 2.2: Enum With Empty enum_values Should Fail
            # ----------------------------------------------------------------
            self.subtest_header("2.2 Enum With Empty enum_values")

            response = self.create_state_variable_raw(
                story_id, 1,
                {"key": "empty_enum", "value_type": "enum", "enum_values": []}
            )

            if response.status_code == 200:
                self.record_test(
                    "enum_rejects_empty_values",
                    False,
                    "Should have rejected enum with empty enum_values"
                )
            else:
                self.record_test(
                    "enum_rejects_empty_values",
                    True,
                    f"Correctly rejected empty enum_values (status {response.status_code})"
                )

            # ----------------------------------------------------------------
            # TEST 2.3: Boolean With Valid Default
            # ----------------------------------------------------------------
            self.subtest_header("2.3 Boolean With Valid Defaults")

            bool_true = self.create_state_variable(
                story_id, 1,
                key="flag_true",
                value_type="boolean",
                default_value=True
            )

            bool_false = self.create_state_variable(
                story_id, 1,
                key="flag_false",
                value_type="boolean",
                default_value=False
            )

            if bool_true["default_value"] != True:
                raise Exception("True default not preserved")
            if bool_false["default_value"] != False:
                raise Exception("False default not preserved")

            self.record_test(
                "boolean_valid_defaults",
                True,
                f"Boolean accepts True and False defaults"
            )

            # ----------------------------------------------------------------
            # TEST 2.4: Number With Various Defaults
            # ----------------------------------------------------------------
            self.subtest_header("2.4 Number With Various Defaults")

            num_zero = self.create_state_variable(
                story_id, 1,
                key="num_zero",
                value_type="number",
                default_value=0
            )

            num_positive = self.create_state_variable(
                story_id, 1,
                key="num_positive",
                value_type="number",
                default_value=100
            )

            num_negative = self.create_state_variable(
                story_id, 1,
                key="num_negative",
                value_type="number",
                default_value=-50
            )

            num_float = self.create_state_variable(
                story_id, 1,
                key="num_float",
                value_type="number",
                default_value=3.14
            )

            if num_zero["default_value"] != 0:
                raise Exception("Zero default not preserved")
            if num_positive["default_value"] != 100:
                raise Exception("Positive default not preserved")
            if num_negative["default_value"] != -50:
                raise Exception("Negative default not preserved")
            if abs(num_float["default_value"] - 3.14) > 0.001:
                raise Exception("Float default not preserved")

            self.record_test(
                "number_valid_defaults",
                True,
                f"Number accepts 0, positive, negative, and float defaults"
            )

            # ----------------------------------------------------------------
            # TEST 2.5: String With Various Defaults
            # ----------------------------------------------------------------
            self.subtest_header("2.5 String With Various Defaults")

            str_empty = self.create_state_variable(
                story_id, 1,
                key="str_empty",
                value_type="string",
                default_value=""
            )

            str_normal = self.create_state_variable(
                story_id, 1,
                key="str_normal",
                value_type="string",
                default_value="Hello World"
            )

            str_special = self.create_state_variable(
                story_id, 1,
                key="str_special",
                value_type="string",
                default_value="Line1\nLine2\tTabbed"
            )

            if str_empty["default_value"] != "":
                raise Exception("Empty string default not preserved")
            if str_normal["default_value"] != "Hello World":
                raise Exception("Normal string default not preserved")
            if str_special["default_value"] != "Line1\nLine2\tTabbed":
                raise Exception("Special chars in string default not preserved")

            self.record_test(
                "string_valid_defaults",
                True,
                f"String accepts empty, normal, and special char defaults"
            )

            # ----------------------------------------------------------------
            # TEST 2.6: Enum With Valid enum_values
            # ----------------------------------------------------------------
            self.subtest_header("2.6 Enum With Valid enum_values")

            enum_var = self.create_state_variable(
                story_id, 1,
                key="difficulty",
                value_type="enum",
                enum_values=["easy", "medium", "hard", "nightmare"],
                default_value="medium"
            )

            if enum_var["enum_values"] != ["easy", "medium", "hard", "nightmare"]:
                raise Exception("Enum values not preserved")
            if enum_var["default_value"] != "medium":
                raise Exception("Enum default not preserved")

            self.record_test(
                "enum_valid_values",
                True,
                f"Enum accepts valid enum_values array"
            )

        except Exception as e:
            self.record_test(
                "value_type_validation",
                False,
                str(e)
            )

    # ========================================================================
    # TEST GROUP 3: Undefined Variable Validation
    # ========================================================================

    def test_undefined_variable_validation(self):
        """Test validation detects undefined variables in choices."""
        self.test_header(
            "Test Group 3: Undefined Variable Validation",
            "Verify validation catches undefined state variables"
        )

        try:
            story = self.create_story(
                "Undefined Variable Test",
                "Testing undefined variable detection"
            )
            story_id = story["id"]
            test_entities["undefined_story_id"] = story_id

            # Define only ONE variable
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

            # ----------------------------------------------------------------
            # TEST 3.1: Undefined in sets_state
            # ----------------------------------------------------------------
            self.subtest_header("3.1 Undefined Variables in sets_state")

            self.create_choice(
                start_node["id"], end_node["id"],
                "Choice with undefined sets_state",
                sets_state={
                    "defined_var": True,
                    "undefined_setter_1": "value",
                    "undefined_setter_2": 42
                }
            )

            validation = self.validate_state_schema(story_id, 1)

            undefined = set(validation.get("undefined_variables", []))
            if "undefined_setter_1" not in undefined:
                raise Exception("Missing undefined_setter_1 in report")
            if "undefined_setter_2" not in undefined:
                raise Exception("Missing undefined_setter_2 in report")

            self.record_test(
                "detect_undefined_in_sets_state",
                True,
                f"Detected undefined vars in sets_state: {undefined}"
            )

            # ----------------------------------------------------------------
            # TEST 3.2: Undefined in requires_state
            # ----------------------------------------------------------------
            self.subtest_header("3.2 Undefined Variables in requires_state")

            # Create another story for clean test
            story2 = self.create_story(
                "Requires State Test",
                "Testing requires_state undefined detection"
            )
            story2_id = story2["id"]

            self.create_state_variable(story2_id, 1, key="defined_req", value_type="boolean")

            start2 = self.create_node(story2_id, "Start", "Begin", is_start=True)
            end2 = self.create_node(story2_id, "End", "End", is_end=True)

            self.create_choice(
                start2["id"], end2["id"],
                "Choice with undefined requires_state",
                requires_state={
                    "defined_req": True,
                    "undefined_req_1": True,
                    "undefined_req_2": "specific_value"
                }
            )

            validation2 = self.validate_state_schema(story2_id, 1)

            undefined2 = set(validation2.get("undefined_variables", []))
            if "undefined_req_1" not in undefined2:
                raise Exception("Missing undefined_req_1 in report")
            if "undefined_req_2" not in undefined2:
                raise Exception("Missing undefined_req_2 in report")

            self.record_test(
                "detect_undefined_in_requires_state",
                True,
                f"Detected undefined vars in requires_state: {undefined2}"
            )

            # ----------------------------------------------------------------
            # TEST 3.3: Validation Reports Error Details
            # ----------------------------------------------------------------
            self.subtest_header("3.3 Validation Error Details")

            errors = validation.get("errors", [])
            if len(errors) == 0:
                raise Exception("Expected error details in validation result")

            # Check error structure
            sample_error = errors[0]
            required_fields = ["variable_key", "used_in", "choice_id", "choice_text", "from_node_id"]
            for field in required_fields:
                if field not in sample_error:
                    raise Exception(f"Missing field in error: {field}")

            self.record_test(
                "validation_error_details",
                True,
                f"Error details include: {', '.join(required_fields)}"
            )

            # ----------------------------------------------------------------
            # TEST 3.4: Defined Variables Are Recognized
            # ----------------------------------------------------------------
            self.subtest_header("3.4 Defined Variables Recognized")

            defined = validation.get("defined_variables", [])
            if "defined_var" not in defined:
                raise Exception("defined_var should be in defined_variables list")

            self.record_test(
                "recognize_defined_variables",
                True,
                f"Correctly recognized defined variable"
            )

            # ----------------------------------------------------------------
            # TEST 3.5: Used Variables Are Tracked
            # ----------------------------------------------------------------
            self.subtest_header("3.5 Used Variables Tracked")

            used = set(validation.get("used_variables", []))
            expected_used = {"defined_var", "undefined_setter_1", "undefined_setter_2"}
            if not expected_used.issubset(used):
                raise Exception(f"Missing used variables. Expected {expected_used}, got {used}")

            self.record_test(
                "track_used_variables",
                True,
                f"Tracked all used variables: {used}"
            )

        except Exception as e:
            self.record_test(
                "undefined_variable_validation",
                False,
                str(e)
            )

    # ========================================================================
    # TEST GROUP 4: Valid Schema (No Errors)
    # ========================================================================

    def test_valid_schema(self):
        """Test validation passes when all variables are defined."""
        self.test_header(
            "Test Group 4: Valid Schema Validation",
            "Verify validation passes with fully defined schema"
        )

        try:
            story = self.create_story(
                "Valid Schema Test",
                "Testing validation with complete schema"
            )
            story_id = story["id"]
            test_entities["valid_story_id"] = story_id

            # ----------------------------------------------------------------
            # TEST 4.1: Empty Schema, No Choices Using State
            # ----------------------------------------------------------------
            self.subtest_header("4.1 Empty Schema, No State Usage")

            start = self.create_node(story_id, "Start", "Begin...", is_start=True)
            end = self.create_node(story_id, "End", "Finish.", is_end=True)

            # Choice without any state
            self.create_choice(start["id"], end["id"], "Simple choice")

            validation = self.validate_state_schema(story_id, 1)

            if not validation.get("is_valid", False):
                raise Exception("Empty schema with no state usage should be valid")

            self.record_test(
                "empty_schema_valid",
                True,
                f"Empty schema with no state usage passes validation"
            )

            # ----------------------------------------------------------------
            # TEST 4.2: Fully Defined Schema
            # ----------------------------------------------------------------
            self.subtest_header("4.2 Fully Defined Schema")

            # Create new story for clean test
            story2 = self.create_story(
                "Fully Defined Schema Test",
                "All variables defined"
            )
            story2_id = story2["id"]

            # Define ALL variables that will be used
            self.create_state_variable(story2_id, 1, key="path", value_type="string")
            self.create_state_variable(story2_id, 1, key="courage", value_type="number", default_value=0)
            self.create_state_variable(story2_id, 1, key="has_sword", value_type="boolean", default_value=False)
            self.create_state_variable(story2_id, 1, key="faction", value_type="enum",
                                       enum_values=["good", "evil", "neutral"])

            # Create nodes
            s = self.create_node(story2_id, "Start", "Begin...", is_start=True)
            m = self.create_node(story2_id, "Middle", "Continue...")
            e = self.create_node(story2_id, "End", "Finish.", is_end=True)

            # Create choices using ONLY defined variables
            self.create_choice(s["id"], m["id"], "Take the brave path",
                             sets_state={"path": "brave", "courage": 10, "faction": "good"})
            self.create_choice(m["id"], e["id"], "Draw the sword",
                             requires_state={"courage": 10},
                             sets_state={"has_sword": True})

            validation2 = self.validate_state_schema(story2_id, 1)

            if not validation2.get("is_valid", False):
                errors = validation2.get("errors", [])
                raise Exception(f"Should have passed, but got errors: {errors}")

            undefined = validation2.get("undefined_variables", [])
            if len(undefined) > 0:
                raise Exception(f"Should have no undefined variables, got: {undefined}")

            self.record_test(
                "fully_defined_schema_valid",
                True,
                f"Fully defined schema passes with 0 undefined variables"
            )

            # ----------------------------------------------------------------
            # TEST 4.3: Multiple Choices All Using Defined Variables
            # ----------------------------------------------------------------
            self.subtest_header("4.3 Multiple Choices, All Defined")

            story3 = self.create_story(
                "Multi-Choice Valid Test",
                "Multiple choices all using defined vars"
            )
            story3_id = story3["id"]

            # Define variables
            self.create_state_variable(story3_id, 1, key="score", value_type="number", default_value=0)
            self.create_state_variable(story3_id, 1, key="visited_cave", value_type="boolean")
            self.create_state_variable(story3_id, 1, key="visited_forest", value_type="boolean")
            self.create_state_variable(story3_id, 1, key="visited_town", value_type="boolean")

            # Create branching structure
            hub = self.create_node(story3_id, "Hub", "Choose your destination", is_start=True)
            cave = self.create_node(story3_id, "Cave", "A dark cave...")
            forest = self.create_node(story3_id, "Forest", "A dense forest...")
            town = self.create_node(story3_id, "Town", "A bustling town...")
            finale = self.create_node(story3_id, "Finale", "Your journey ends.", is_end=True)

            # Multiple choices from hub
            self.create_choice(hub["id"], cave["id"], "Enter the cave",
                             sets_state={"visited_cave": True, "score": 10})
            self.create_choice(hub["id"], forest["id"], "Walk into the forest",
                             sets_state={"visited_forest": True, "score": 20})
            self.create_choice(hub["id"], town["id"], "Visit the town",
                             sets_state={"visited_town": True, "score": 5})

            # Conditional choices to finale
            self.create_choice(cave["id"], finale["id"], "Exit cave",
                             requires_state={"visited_cave": True})
            self.create_choice(forest["id"], finale["id"], "Leave forest",
                             requires_state={"visited_forest": True})
            self.create_choice(town["id"], finale["id"], "Depart town",
                             requires_state={"visited_town": True})

            validation3 = self.validate_state_schema(story3_id, 1)

            if not validation3.get("is_valid", False):
                raise Exception(f"Multi-choice story should be valid")

            used = set(validation3.get("used_variables", []))
            expected = {"score", "visited_cave", "visited_forest", "visited_town"}
            if not expected.issubset(used):
                raise Exception(f"Not all expected variables tracked as used")

            self.record_test(
                "multi_choice_all_defined",
                True,
                f"6 choices across 4 locations, all variables defined"
            )

        except Exception as e:
            self.record_test(
                "valid_schema",
                False,
                str(e)
            )

    # ========================================================================
    # TEST GROUP 5: Complex Validation Scenarios
    # ========================================================================

    def test_complex_validation_scenarios(self):
        """Test complex multi-node, multi-choice validation scenarios."""
        self.test_header(
            "Test Group 5: Complex Validation Scenarios",
            "Multi-node stories with mixed defined/undefined variables"
        )

        try:
            # ----------------------------------------------------------------
            # TEST 5.1: Some Choices Valid, Some Invalid
            # ----------------------------------------------------------------
            self.subtest_header("5.1 Mixed Valid/Invalid Choices")

            story = self.create_story(
                "Mixed Validity Test",
                "Some choices use undefined vars, some don't"
            )
            story_id = story["id"]

            # Define only some variables
            self.create_state_variable(story_id, 1, key="defined_1", value_type="boolean")
            self.create_state_variable(story_id, 1, key="defined_2", value_type="number")

            start = self.create_node(story_id, "Start", "Begin", is_start=True)
            branch_a = self.create_node(story_id, "Branch A", "Path A")
            branch_b = self.create_node(story_id, "Branch B", "Path B")
            end = self.create_node(story_id, "End", "End", is_end=True)

            # Valid choice (uses only defined vars)
            self.create_choice(start["id"], branch_a["id"], "Valid choice",
                             sets_state={"defined_1": True, "defined_2": 100})

            # Invalid choice (uses undefined var)
            self.create_choice(start["id"], branch_b["id"], "Invalid choice",
                             sets_state={"defined_1": True, "undefined_var": "oops"})

            # Valid endings
            self.create_choice(branch_a["id"], end["id"], "End A",
                             requires_state={"defined_1": True})
            self.create_choice(branch_b["id"], end["id"], "End B",
                             requires_state={"undefined_condition": True})  # Invalid

            validation = self.validate_state_schema(story_id, 1)

            if validation.get("is_valid", True):
                raise Exception("Should be invalid due to undefined variables")

            undefined = set(validation.get("undefined_variables", []))
            if "undefined_var" not in undefined:
                raise Exception("Missing undefined_var")
            if "undefined_condition" not in undefined:
                raise Exception("Missing undefined_condition")

            # defined vars should still be recognized
            defined = validation.get("defined_variables", [])
            if "defined_1" not in defined or "defined_2" not in defined:
                raise Exception("Defined variables not recognized")

            self.record_test(
                "mixed_valid_invalid_choices",
                True,
                f"Detected 2 undefined vars while recognizing 2 defined vars"
            )

            # ----------------------------------------------------------------
            # TEST 5.2: Deep Branching with State
            # ----------------------------------------------------------------
            self.subtest_header("5.2 Deep Branching with State")

            story2 = self.create_story(
                "Deep Branching Test",
                "3 levels deep with state tracking"
            )
            story2_id = story2["id"]

            # Define some vars, leave others undefined
            self.create_state_variable(story2_id, 1, key="level", value_type="number")
            self.create_state_variable(story2_id, 1, key="path_taken", value_type="string")
            # NOT defining: "secret_found", "treasure_value"

            # Level 1
            l1 = self.create_node(story2_id, "Level 1", "Start", is_start=True)
            # Level 2
            l2_a = self.create_node(story2_id, "Level 2A", "Path A")
            l2_b = self.create_node(story2_id, "Level 2B", "Path B")
            # Level 3
            l3_a1 = self.create_node(story2_id, "Level 3A1", "End A1", is_end=True)
            l3_a2 = self.create_node(story2_id, "Level 3A2", "End A2", is_end=True)
            l3_b1 = self.create_node(story2_id, "Level 3B1", "End B1", is_end=True)

            # Level 1 -> Level 2 (valid)
            self.create_choice(l1["id"], l2_a["id"], "Go to A",
                             sets_state={"level": 2, "path_taken": "A"})
            self.create_choice(l1["id"], l2_b["id"], "Go to B",
                             sets_state={"level": 2, "path_taken": "B"})

            # Level 2 -> Level 3 (mix of valid/invalid)
            self.create_choice(l2_a["id"], l3_a1["id"], "Find secret",
                             sets_state={"level": 3, "secret_found": True})  # undefined!
            self.create_choice(l2_a["id"], l3_a2["id"], "Skip secret",
                             sets_state={"level": 3})  # valid
            self.create_choice(l2_b["id"], l3_b1["id"], "Find treasure",
                             sets_state={"level": 3, "treasure_value": 1000})  # undefined!

            validation2 = self.validate_state_schema(story2_id, 1)

            undefined2 = set(validation2.get("undefined_variables", []))
            if "secret_found" not in undefined2:
                raise Exception("Missing secret_found in undefined")
            if "treasure_value" not in undefined2:
                raise Exception("Missing treasure_value in undefined")

            self.record_test(
                "deep_branching_validation",
                True,
                f"Detected undefined vars at depth 3: {undefined2}"
            )

            # ----------------------------------------------------------------
            # TEST 5.3: Same Variable Used Multiple Times
            # ----------------------------------------------------------------
            self.subtest_header("5.3 Same Variable Used Multiple Times")

            story3 = self.create_story(
                "Repeated Variable Test",
                "Same var used in multiple choices"
            )
            story3_id = story3["id"]

            # Define one var
            self.create_state_variable(story3_id, 1, key="points", value_type="number")
            # Leave "bonus" undefined

            start3 = self.create_node(story3_id, "Start", "Begin", is_start=True)
            mid3 = self.create_node(story3_id, "Middle", "Middle", )
            end3 = self.create_node(story3_id, "End", "End", is_end=True)

            # Use "bonus" in multiple places
            self.create_choice(start3["id"], mid3["id"], "Choice 1",
                             sets_state={"points": 10, "bonus": 5})
            self.create_choice(mid3["id"], end3["id"], "Choice 2",
                             sets_state={"points": 20, "bonus": 10})

            validation3 = self.validate_state_schema(story3_id, 1)

            # Should report "bonus" as undefined
            undefined3 = validation3.get("undefined_variables", [])
            if "bonus" not in undefined3:
                raise Exception("Should report 'bonus' as undefined")

            # Should have multiple errors for the same variable
            errors3 = [e for e in validation3.get("errors", []) if e["variable_key"] == "bonus"]
            if len(errors3) < 2:
                raise Exception(f"Should have 2 errors for 'bonus', got {len(errors3)}")

            self.record_test(
                "same_variable_multiple_uses",
                True,
                f"Detected 'bonus' undefined in {len(errors3)} places"
            )

        except Exception as e:
            self.record_test(
                "complex_validation_scenarios",
                False,
                str(e)
            )

    # ========================================================================
    # TEST GROUP 6: Publish Integration
    # ========================================================================

    def test_publish_integration(self):
        """Test publishing behavior with state schema validation."""
        self.test_header(
            "Test Group 6: Publish Integration",
            "Soft block on publish with undefined variables"
        )

        try:
            # ----------------------------------------------------------------
            # TEST 6.1: Publish Succeeds with Valid Schema
            # ----------------------------------------------------------------
            self.subtest_header("6.1 Publish with Valid Schema")

            story = self.create_story(
                "Publish Valid Schema Test",
                "Should publish successfully"
            )
            story_id = story["id"]

            # Define all needed variables
            self.create_state_variable(story_id, 1, key="completed", value_type="boolean")

            start = self.create_node(story_id, "Start", "Begin", is_start=True)
            end = self.create_node(story_id, "End", "End", is_end=True)

            self.create_choice(start["id"], end["id"], "Finish",
                             sets_state={"completed": True})

            success, response = self.publish_story(story_id)

            if not success:
                raise Exception(f"Publish should have succeeded: {response}")

            self.record_test(
                "publish_valid_schema",
                True,
                f"Story published successfully with valid schema"
            )

            # ----------------------------------------------------------------
            # TEST 6.2: Publish with Undefined Variables (Soft Block)
            # ----------------------------------------------------------------
            self.subtest_header("6.2 Publish with Undefined Variables")

            story2 = self.create_story(
                "Publish Invalid Schema Test",
                "Should soft-block on undefined vars"
            )
            story2_id = story2["id"]

            # Only define ONE variable
            self.create_state_variable(story2_id, 1, key="defined_only", value_type="boolean")

            start2 = self.create_node(story2_id, "Start", "Begin", is_start=True)
            end2 = self.create_node(story2_id, "End", "End", is_end=True)

            # Use undefined variable
            self.create_choice(start2["id"], end2["id"], "Bad choice",
                             sets_state={"defined_only": True, "undefined_blocker": "oops"})

            success2, response2 = self.publish_story(story2_id)

            # The behavior depends on implementation:
            # Option A: Publish fails (422) with undefined vars list
            # Option B: Publish succeeds but returns warning
            # We'll check both scenarios

            if not success2:
                # Publish was blocked - this is the "soft block" behavior
                self.record_test(
                    "publish_blocked_undefined_vars",
                    True,
                    f"Publish correctly blocked due to undefined variables"
                )
            else:
                # Publish succeeded - check if it's the story we expected
                # (some implementations allow publish with warnings)
                if response2.get("is_published"):
                    self.record_test(
                        "publish_blocked_undefined_vars",
                        False,
                        f"Publish should have been blocked, but story was published"
                    )
                else:
                    self.record_test(
                        "publish_blocked_undefined_vars",
                        True,
                        f"Publish returned without marking as published (soft block)"
                    )

            # ----------------------------------------------------------------
            # TEST 6.3: Validation Before Publish
            # ----------------------------------------------------------------
            self.subtest_header("6.3 Pre-Publish Validation Check")

            # Always validate before attempting publish
            validation = self.validate_state_schema(story2_id, 1)

            if validation.get("is_valid", True):
                raise Exception("Validation should fail for story with undefined vars")

            undefined = validation.get("undefined_variables", [])
            if "undefined_blocker" not in undefined:
                raise Exception("Should report undefined_blocker")

            self.record_test(
                "pre_publish_validation",
                True,
                f"Pre-publish validation correctly identifies issues"
            )

        except Exception as e:
            self.record_test(
                "publish_integration",
                False,
                str(e)
            )

    # ========================================================================
    # TEST GROUP 7: Edge Cases
    # ========================================================================

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        self.test_header(
            "Test Group 7: Edge Cases",
            "Boundary conditions, special characters, limits"
        )

        try:
            story = self.create_story(
                "Edge Cases Test",
                "Testing boundary conditions"
            )
            story_id = story["id"]

            # ----------------------------------------------------------------
            # TEST 7.1: Variable Key with Underscores
            # ----------------------------------------------------------------
            self.subtest_header("7.1 Keys with Underscores")

            var = self.create_state_variable(
                story_id, 1,
                key="player_health_points",
                value_type="number"
            )

            if var["key"] != "player_health_points":
                raise Exception("Underscore key not preserved")

            self.record_test(
                "key_with_underscores",
                True,
                f"Key 'player_health_points' accepted"
            )

            # ----------------------------------------------------------------
            # TEST 7.2: Variable Key with Numbers
            # ----------------------------------------------------------------
            self.subtest_header("7.2 Keys with Numbers")

            var2 = self.create_state_variable(
                story_id, 1,
                key="level_2_complete",
                value_type="boolean"
            )

            if var2["key"] != "level_2_complete":
                raise Exception("Key with numbers not preserved")

            self.record_test(
                "key_with_numbers",
                True,
                f"Key 'level_2_complete' accepted"
            )

            # ----------------------------------------------------------------
            # TEST 7.3: Long Description
            # ----------------------------------------------------------------
            self.subtest_header("7.3 Long Description")

            long_desc = "A" * 400  # Near max length
            var3 = self.create_state_variable(
                story_id, 1,
                key="long_desc_var",
                value_type="string",
                description=long_desc
            )

            if len(var3["description"]) != 400:
                raise Exception("Long description truncated")

            self.record_test(
                "long_description",
                True,
                f"400-character description accepted"
            )

            # ----------------------------------------------------------------
            # TEST 7.4: Many Enum Values
            # ----------------------------------------------------------------
            self.subtest_header("7.4 Many Enum Values")

            many_values = [f"option_{i}" for i in range(20)]
            var4 = self.create_state_variable(
                story_id, 1,
                key="many_options",
                value_type="enum",
                enum_values=many_values
            )

            if len(var4["enum_values"]) != 20:
                raise Exception("Not all enum values preserved")

            self.record_test(
                "many_enum_values",
                True,
                f"Enum with 20 values accepted"
            )

            # ----------------------------------------------------------------
            # TEST 7.5: Category Organization
            # ----------------------------------------------------------------
            self.subtest_header("7.5 Category Organization")

            self.create_state_variable(story_id, 1, key="stat_str", value_type="number", category="stats")
            self.create_state_variable(story_id, 1, key="stat_dex", value_type="number", category="stats")
            self.create_state_variable(story_id, 1, key="item_sword", value_type="boolean", category="inventory")
            self.create_state_variable(story_id, 1, key="item_shield", value_type="boolean", category="inventory")

            schema = self.get_state_schema(story_id, 1)
            data = schema.get("data", [])

            stats_vars = [v for v in data if v.get("category") == "stats"]
            inventory_vars = [v for v in data if v.get("category") == "inventory"]

            if len(stats_vars) != 2:
                raise Exception(f"Expected 2 stats vars, got {len(stats_vars)}")
            if len(inventory_vars) != 2:
                raise Exception(f"Expected 2 inventory vars, got {len(inventory_vars)}")

            self.record_test(
                "category_organization",
                True,
                f"Variables organized by category (2 stats, 2 inventory)"
            )

            # ----------------------------------------------------------------
            # TEST 7.6: No Nodes/Choices (Empty Story Validation)
            # ----------------------------------------------------------------
            self.subtest_header("7.6 Empty Story Validation")

            empty_story = self.create_story(
                "Empty Story Test",
                "No nodes or choices"
            )
            empty_id = empty_story["id"]

            # Add variables but no nodes/choices
            self.create_state_variable(empty_id, 1, key="unused_var", value_type="boolean")

            validation = self.validate_state_schema(empty_id, 1)

            # Should be valid (no undefined vars since no choices use any vars)
            if not validation.get("is_valid", False):
                raise Exception("Empty story should have valid schema")

            used = validation.get("used_variables", [])
            if len(used) != 0:
                raise Exception(f"No variables should be used, got {used}")

            self.record_test(
                "empty_story_validation",
                True,
                f"Empty story validates with 0 used variables"
            )

            # ----------------------------------------------------------------
            # TEST 7.7: Unicode in String Default
            # ----------------------------------------------------------------
            self.subtest_header("7.7 Unicode in String Default")

            var_unicode = self.create_state_variable(
                story_id, 1,
                key="greeting",
                value_type="string",
                default_value="Hello, 世界! 🌍"
            )

            if var_unicode["default_value"] != "Hello, 世界! 🌍":
                raise Exception("Unicode default not preserved")

            self.record_test(
                "unicode_string_default",
                True,
                f"Unicode characters preserved in default value"
            )

        except Exception as e:
            self.record_test(
                "edge_cases",
                False,
                str(e)
            )

    # ========================================================================
    # TEST GROUP 8: Error Handling
    # ========================================================================

    def test_error_handling(self):
        """Test error handling for invalid operations."""
        self.test_header(
            "Test Group 8: Error Handling",
            "Invalid operations and error responses"
        )

        try:
            story = self.create_story(
                "Error Handling Test",
                "Testing error responses"
            )
            story_id = story["id"]

            # ----------------------------------------------------------------
            # TEST 8.1: Get Schema for Non-existent Story
            # ----------------------------------------------------------------
            self.subtest_header("8.1 Non-existent Story")

            fake_uuid = "00000000-0000-0000-0000-000000000000"
            response = self.session.get(
                f"{BASE_URL}/stories/{fake_uuid}/versions/1/state-schema"
            )

            if response.status_code == 200:
                self.record_test(
                    "nonexistent_story_error",
                    False,
                    "Should return error for non-existent story"
                )
            else:
                self.record_test(
                    "nonexistent_story_error",
                    True,
                    f"Correctly returned {response.status_code} for non-existent story"
                )

            # ----------------------------------------------------------------
            # TEST 8.2: Update Non-existent Variable
            # ----------------------------------------------------------------
            self.subtest_header("8.2 Update Non-existent Variable")

            response = self.session.put(
                f"{BASE_URL}/stories/{story_id}/versions/1/state-schema/{fake_uuid}",
                json={"description": "updated"}
            )

            if response.status_code == 200:
                self.record_test(
                    "nonexistent_variable_error",
                    False,
                    "Should return error for non-existent variable"
                )
            else:
                self.record_test(
                    "nonexistent_variable_error",
                    True,
                    f"Correctly returned {response.status_code} for non-existent variable"
                )

            # ----------------------------------------------------------------
            # TEST 8.3: Delete Non-existent Variable
            # ----------------------------------------------------------------
            self.subtest_header("8.3 Delete Non-existent Variable")

            response = self.session.delete(
                f"{BASE_URL}/stories/{story_id}/versions/1/state-schema/{fake_uuid}"
            )

            if response.status_code in [200, 204]:
                self.record_test(
                    "delete_nonexistent_error",
                    False,
                    "Should return error for non-existent variable"
                )
            else:
                self.record_test(
                    "delete_nonexistent_error",
                    True,
                    f"Correctly returned {response.status_code} for non-existent variable"
                )

            # ----------------------------------------------------------------
            # TEST 8.4: Create Variable with Missing Key
            # ----------------------------------------------------------------
            self.subtest_header("8.4 Missing Required Field (key)")

            response = self.create_state_variable_raw(
                story_id, 1,
                {"value_type": "boolean"}  # missing "key"
            )

            if response.status_code == 200:
                self.record_test(
                    "missing_key_error",
                    False,
                    "Should reject variable without key"
                )
            else:
                self.record_test(
                    "missing_key_error",
                    True,
                    f"Correctly rejected missing key (status {response.status_code})"
                )

            # ----------------------------------------------------------------
            # TEST 8.5: Create Variable with Invalid Value Type
            # ----------------------------------------------------------------
            self.subtest_header("8.5 Invalid Value Type")

            response = self.create_state_variable_raw(
                story_id, 1,
                {"key": "bad_type", "value_type": "invalid_type"}
            )

            if response.status_code == 200:
                self.record_test(
                    "invalid_value_type_error",
                    False,
                    "Should reject invalid value_type"
                )
            else:
                self.record_test(
                    "invalid_value_type_error",
                    True,
                    f"Correctly rejected invalid value_type (status {response.status_code})"
                )

            # ----------------------------------------------------------------
            # TEST 8.6: Empty Key String
            # ----------------------------------------------------------------
            self.subtest_header("8.6 Empty Key String")

            response = self.create_state_variable_raw(
                story_id, 1,
                {"key": "", "value_type": "boolean"}
            )

            if response.status_code == 200:
                self.record_test(
                    "empty_key_error",
                    False,
                    "Should reject empty key"
                )
            else:
                self.record_test(
                    "empty_key_error",
                    True,
                    f"Correctly rejected empty key (status {response.status_code})"
                )

        except Exception as e:
            self.record_test(
                "error_handling",
                False,
                str(e)
            )

    # ========================================================================
    # Main Test Runner
    # ========================================================================

    def run_all_tests(self, test_filter: str = None):
        """Run all state schema tests."""
        self.test_header(
            "STORY STATE SCHEMA E2E TEST SUITE",
            "Comprehensive StoryStateVariable testing"
        )

        try:
            # Authenticate
            self.authenticate()

            # Define test groups
            test_groups = {
                "crud": self.test_state_variable_crud,
                "types": self.test_value_type_validation,
                "undefined": self.test_undefined_variable_validation,
                "valid": self.test_valid_schema,
                "complex": self.test_complex_validation_scenarios,
                "publish": self.test_publish_integration,
                "edge": self.test_edge_cases,
                "errors": self.test_error_handling,
            }

            # Run filtered or all tests
            if test_filter and test_filter in test_groups:
                test_groups[test_filter]()
            else:
                for test_func in test_groups.values():
                    test_func()

        except Exception as e:
            self.log(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return False

        return test_results["failed"] == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="E2E tests for Story State Schema"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--test", "-t",
                       choices=["crud", "types", "undefined", "valid", "complex", "publish", "edge", "errors"],
                       help="Run specific test group only")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  STORY STATE SCHEMA E2E TEST SUITE")
    print("  Comprehensive StoryStateVariable testing")
    print("=" * 70)

    try:
        # Get authenticated session
        session = get_authenticated_session()

        # Create test runner
        runner = TestRunner(session, verbose=args.verbose)

        # Run tests
        success = runner.run_all_tests(test_filter=args.test)

        # Calculate results
        test_results["end_time"] = datetime.now().isoformat()
        start = datetime.fromisoformat(test_results["start_time"])
        end = datetime.fromisoformat(test_results["end_time"])
        test_results["duration_seconds"] = (end - start).total_seconds()

        if test_results["total_tests"] > 0:
            rate = (test_results["passed"] / test_results["total_tests"]) * 100
            test_results["success_rate"] = f"{rate:.1f}%"

        test_results["test_entities"] = test_entities

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

        # Show failed tests if any
        if test_results["failed"] > 0:
            print("\n  Failed Tests:")
            for test in test_results["tests"]:
                if not test["passed"]:
                    print(f"    ❌ {test['name']}: {test['message']}")

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
