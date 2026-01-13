#!/usr/bin/env python3
"""
[FEATURE] E2E Test Suite

Comprehensive tests for [FEATURE] functionality:
- [Test area 1]
- [Test area 2]
- [Test area 3]

Usage:
    python test_[feature].py
    python test_[feature].py --verbose
    python test_[feature].py --test [group]

Output:
    test_results_[feature].json
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

import requests

# Import auth helper - adjust path as needed
sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session, AuthenticationError


# Configuration
BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "test_results_[feature].json"

# Test state
test_results = {
    "test_suite": "[Feature] E2E Test Suite",
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

test_entities = {}  # Stores created entity IDs for cleanup/reference


class TestRunner:
    """Runs [feature] tests."""

    def __init__(self, session: requests.Session, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.user = None

    # ========================================================================
    # Logging & Output
    # ========================================================================

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

    # ========================================================================
    # Setup & Authentication
    # ========================================================================

    def authenticate(self):
        """Authenticate and get user info."""
        self.debug(f"GET {BASE_URL}/users/me")
        response = self.session.get(f"{BASE_URL}/users/me")

        if response.status_code == 200:
            user_data = response.json()
            self.user = user_data
            print(f"  ✅ Authenticated as: {user_data.get('email')}")
        else:
            raise Exception(f"Failed to get user info: {response.text}")

    # ========================================================================
    # API Helpers - Add your resource-specific helpers here
    # ========================================================================

    def create_resource(self, name: str, **kwargs) -> dict:
        """Create a resource and return its data."""
        payload = {"name": name, **kwargs}

        self.debug(f"POST {BASE_URL}/resources")
        self.debug(f"Payload: {json.dumps(payload, indent=2)}")

        response = self.session.post(f"{BASE_URL}/resources", json=payload)

        self.debug(f"Response status: {response.status_code}")
        self.debug(f"Response body: {response.text[:500]}")

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create resource: {response.text}")

        return response.json()

    def get_resource(self, resource_id: str) -> dict:
        """Get a resource by ID."""
        self.debug(f"GET {BASE_URL}/resources/{resource_id}")

        response = self.session.get(f"{BASE_URL}/resources/{resource_id}")

        if response.status_code != 200:
            raise Exception(f"Failed to get resource: {response.text}")

        return response.json()

    # ========================================================================
    # TEST GROUP 1: Basic CRUD
    # ========================================================================

    def test_basic_crud(self):
        """Test basic CRUD operations."""
        self.test_header(
            "Test Group 1: Basic CRUD",
            "Create, read, update, delete operations"
        )

        try:
            # ----------------------------------------------------------------
            # TEST 1.1: Create Resource
            # ----------------------------------------------------------------
            self.subtest_header("1.1 Create Resource")

            resource = self.create_resource(
                "Test Resource",
                description="Test description"
            )

            if not resource.get("id"):
                raise Exception("Resource missing ID")

            test_entities["resource_id"] = resource["id"]

            self.record_test(
                "create_resource",
                True,
                f"Created resource: {resource['id'][:8]}..."
            )

            # ----------------------------------------------------------------
            # TEST 1.2: Read Resource
            # ----------------------------------------------------------------
            self.subtest_header("1.2 Read Resource")

            fetched = self.get_resource(resource["id"])

            if fetched["id"] != resource["id"]:
                raise Exception("Resource ID mismatch")

            self.record_test(
                "read_resource",
                True,
                f"Retrieved resource successfully"
            )

        except Exception as e:
            self.record_test(
                "basic_crud",
                False,
                str(e)
            )

    # ========================================================================
    # TEST GROUP 2: Integration Scenarios
    # ========================================================================

    def test_integration_scenarios(self):
        """Test integrated workflows."""
        self.test_header(
            "Test Group 2: Integration Scenarios",
            "Multi-step workflows and complex interactions"
        )

        try:
            # ----------------------------------------------------------------
            # TEST 2.1: Complex Workflow
            # ----------------------------------------------------------------
            self.subtest_header("2.1 Complex Workflow")

            # Implement your integration test here...

            self.record_test(
                "complex_workflow",
                True,
                "Workflow completed successfully"
            )

        except Exception as e:
            self.record_test(
                "integration_scenarios",
                False,
                str(e)
            )

    # ========================================================================
    # Main Test Runner
    # ========================================================================

    def run_all_tests(self, test_filter: str = None):
        """Run all tests."""
        self.test_header(
            "[FEATURE] E2E TEST SUITE",
            "Comprehensive [feature] testing"
        )

        try:
            # Authenticate
            self.authenticate()

            # Define test groups
            test_groups = {
                "crud": self.test_basic_crud,
                "integration": self.test_integration_scenarios,
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
        description="E2E tests for [Feature]"
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--test", "-t",
                       choices=["crud", "integration"],
                       help="Run specific test group only")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  [FEATURE] E2E TEST SUITE")
    print("  Comprehensive [feature] testing")
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
