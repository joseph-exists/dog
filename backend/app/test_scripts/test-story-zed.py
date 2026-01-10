import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Import auth helper
sys.path.append(str(Path(__file__).parent))
from app.test_scripts.test_story_system import test_entities
from auth_helper import get_authenticated_session, AuthenticationError


# Configuration
BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "test_results_zed-zed-zed.json"

# Test state
test_results = {
    "test_suite": "zed suite",
    "start_time": None,
    "end_time": None,
    "duration_seconds": 0,
    "stories_created": [],
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "success_rate": "0%",
    "test_entities": {},
    "tests": []
}

test_entities = {}  # Stores created entity IDs

class TestRunner:
    """Runs branching story tests."""

    def __init__(self, session: requests.Session, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.user = None
        self.persona_id = None

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

    def set_auth(self, user_data: dict):
        """Record successful authentication in test results."""
        test_results["authentication"] = {
            "status": "success",
            "user": {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "is_superuser": user_data.get("is_superuser", False)
            }
        }


    def authenticate(self):
        """Authenticate and get user info."""
        self.debug(f"GET {BASE_URL}/users/me")
        response = self.session.get(f"{BASE_URL}/users/me")

        self.debug(f"Response status: {response.status_code}")
        self.debug(f"Response body: {response.text[:500]}")

        if response.status_code == 200:
            user_data = response.json()
            self.set_auth(user_data)
            self.user = user_data
            print(f"  ✅ Authenticated as: {user_data.get('email')}")
        else:
            raise Exception("Failed to get user info")


    def create_test_persona(self, persona_id: str | None = None) -> str:
        """Create or verify test persona (UserPersona for story system)."""
        self.test_header("Test Setup: Creating Test Persona")

        if persona_id:
            # Verify existing user persona
            self.debug(f"GET {BASE_URL}/user-personas/{persona_id}")
            response = self.session.get(f"{BASE_URL}/user-personas/{persona_id}")
            self.debug(f"Response status: {response.status_code}")
            self.debug(f"Response body: {response.text[:500]}")

            if response.status_code == 200:
                user_persona = response.json()
                print(f"  ✅ Using existing UserPersona (ID: {persona_id[:8]}...)")
                return persona_id
            else:
                print(f"  ⚠️  UserPersona {persona_id} not found, creating new one...")

        # Step 1: Create a Persona (template)
        persona_data = {
            "name": f"Test Explorer {datetime.now().strftime('%H%M%S')}",
            "description": "Test persona for story system tests"
        }

        self.debug(f"POST {BASE_URL}/personas")
        self.debug(f"Request payload: {json.dumps(persona_data, indent=2)}")

        response = self.session.post(f"{BASE_URL}/personas", json=persona_data)

        self.debug(f"Response status: {response.status_code}")
        self.debug(f"Response body: {response.text[:500]}")

        if response.status_code != 200:
            print(f"  ❌ Failed to create Persona: {response.text}")
            raise Exception("Could not create Persona template")

        persona = response.json()
        print(f"  ✅ Persona template created: \"{persona['name']}\" (ID: {persona['id'][:8]}...)")

        # Step 2: Create a UserPersona (user's instance of the Persona)
        user_persona_data = {
            "persona_id": persona['id']
        }

        self.debug(f"POST {BASE_URL}/user-personas")
        self.debug(f"Request payload: {json.dumps(user_persona_data, indent=2)}")

        response = self.session.post(f"{BASE_URL}/user-personas", json=user_persona_data)

        self.debug(f"Response status: {response.status_code}")
        self.debug(f"Response body: {response.text[:500]}")

        if response.status_code == 200:
            user_persona = response.json()
            print(f"  ✅ UserPersona created (ID: {user_persona['id'][:8]}...)")
            return user_persona['id']
        else:
            print(f"  ❌ Failed to create UserPersona: {response.text}")
            raise Exception("Could not create UserPersona")


    def create_story(self, title: str, description: str) -> str:
        """Create a story and return its data."""
        self.test_header("Test: creating a story.")

        story_data = {
            "title": title,
            "description": description,
            "current_version": 1
        }

        self.log(f"Creating story: {title}")
        self.debug(f"POST {BASE_URL}/stories")
        self.debug(f"Request payload: {json.dumps(story_data, indent=2)}")

        try:
            response = self.session.post(f"{BASE_URL}/stories",
            json=story_data)

            self.debug(f"Response status: {response.status_code}")
            self.debug(f"Response body: {response.text[:500]}")

            response.raise_for_status()
            story = response.json()

            test_entities["story_id"] = story["id"]

            self.record_test(
                "create_story",
                True,
                f"Story created: \"{story['title']}\" (ID: {story['id'][:8]}...), version {story['current_version']}"
            )
            return story["id"]

        except requests.exceptions.RequestException as e:
            self.debug(f"Exception occurred: {str(e)}")
            self.record_test(
                "create_story",
                False,
                f"HTTP {e.response.status_code if e.response else 'ERROR'}: {e.response.text if e.response else str(e)}"
            )
            raise

    def create_node(self, story_id: str, title: str, content: str,
                   is_start: bool = False, is_end: bool = False) -> dict:
        """Create a story node."""
        payload = {
            "story_id": story_id,
            "story_version": 1,
            "title": title,
            "content": content,
            "node_type": "text",
            "content_format": "text",
            "is_start_node": is_start,
            "is_end_node": is_end
        }

        self.debug(f"Creating node: {title}")
        self.debug(f"POST {BASE_URL}/storynodes")
        self.debug(f"Request payload: {json.dumps(payload, indent=2)}")

        response = self.session.post(
            f"{BASE_URL}/storynodes",
            json=payload
        )

        self.debug(f"Response status: {response.status_code}")
        self.debug(f"Response body: {response.text[:500]}")

        if response.status_code != 200:
            raise Exception(f"Failed to create node {title}: {response.text}")
        return response.json()

    def create_choice(self, from_node_id: str, to_node_id: str, text: str,
                     sets_state: dict = None, requires_state: dict = None,
                     order: int = 0) -> dict:
        """Create a choice between nodes."""
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

        self.debug(f"Creating choice: {text}")
        self.debug(f"POST {BASE_URL}/node-choices")
        self.debug(f"Request payload: {json.dumps(payload, indent=2)}")

        response = self.session.post(
            f"{BASE_URL}/node-choices",
            json=payload
        )

        self.debug(f"Response status: {response.status_code}")
        self.debug(f"Response body: {response.text[:500]}")

        if response.status_code != 200:
            raise Exception(f"Failed to create choice '{text}': {response.text}")
        return response.json()

    def publish_story(self, story_id: str) -> bool:
        """Publish a story."""
        self.log("Publishing story...")
        self.debug(f"PUT {BASE_URL}/stories/{story_id}/publish")
        self.debug("Request payload: (empty body)")

        response = self.session.put(
            f"{BASE_URL}/stories/{story_id}/publish"
        )

        self.debug(f"Response status: {response.status_code}")
        self.debug(f"Response body: {response.text[:500]}")

        if response.status_code != 200:
            raise Exception(f"Failed to publish story: {response.text}")

        story = response.json()
        if not story.get("is_published"):
            raise Exception("Story was not marked as published")

        return True

    def test_story_zero(self):
        """validation of script functions for story flow"""

        self.test_header(
            "Story 0: Test Story Zed"
        )

        try:
            # create story zed
            story_id = self.create_story(
                "Test Story Zed Title",
                "This is Zed Content"
            )

            start = self.create_node(
                story_id,
                "Zed Node One",
                "Zed Node One content.",
                is_start=True
            )    # Left path nodes

            left_1 = self.create_node(
                story_id,
                "Zed left node",
                "ZZzzed llleft nnnnode "
                "zzzed llllelft nnnnnooooodeeee."
            )
            left_end = self.create_node(
                story_id,
                "Zed left end",
                "zed left end "
                "zed lefted ended",
                is_end=True
            )
            # Create choices with state tracking
            self.create_choice(
                start["id"], left_1["id"],
                "who's zed",
                sets_state={"path": "shadow", "courage": 5},
                order=0
            )
            self.create_choice(
                left_1["id"], left_end["id"],
                "maybe zed's dead",
                sets_state={"path": "shadow", "courage": 5},
                order=0
            )
            # Publish story
            if not self.publish_story(story_id):
                raise Exception("Failed to publish story. Zed's dead, baby.  Zed's dead.")

            room = self.create_room("Zed's Room", story_id)

            test_results["stories_created"].append({
                "name": "The Zed",
                "story_id": story_id,
                "room_id": room["room_id"],
                "branches": 3,
                "endings": 3
            })

            self.record_test(
                "zed-test-we-zedded",
                True,
                "Successfully did the zed."
            )

        except Exception as e:
            self.record_test(
                "test_story_zed",
                False,
                str(e)
            )

    def create_room(self, title: str, story_id: str) -> dict:
        """Create a room associated with a story."""
        payload = {
            "title": title,
            "story_id": story_id
        }

        self.log(f"Creating room: {title}")
        self.debug(f"POST {BASE_URL}/rooms")
        self.debug(f"Request payload: {json.dumps(payload, indent=2)}")

        response = self.session.post(
            f"{BASE_URL}/rooms",
            json=payload
        )

        self.debug(f"Response status: {response.status_code}")
        self.debug(f"Response body: {response.text[:500]}")

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create room: {response.text}")

        room = response.json()

        # verify room_id exists
        if 'room_id' not in room:
            raise Exception("response missing 'room_id' field")

        self.debug(f"Room created successfully: {room.get('room_id', 'N/A')[:8]}...")
        return room

    def run_all_tests(self, story_filter: str = None):
        """the zedster"""
        self.test_header(
            "zedediah",
            "zzzzzz eeeeee dddddd"
        )

        try:
            # Authenticate and get user info
            self.authenticate()

            # Get/create persona (use existing if provided via --persona-id)
            self.persona_id = self.create_test_persona(self.persona_id)

            # Run story tests based on filter
            stories_to_test = {
                "zed": self.test_story_zero
            }

            if story_filter and story_filter in stories_to_test:
                stories_to_test[story_filter]()
            else:
                for test_func in stories_to_test.values():
                    test_func()

        except Exception as e:
            self.log(f"Fatal error: {e}")
            return False

        return test_results["failed"] == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="zed zed zed"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--story", choices=["zed"],
                       help="Run specific story test only")
    parser.add_argument("--persona-id", help="Use existing persona ID")
    parser.add_argument("--no-cleanup", action="store_true",
                       help="Keep created entities (don't cleanup)")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  BRANCHING STORIES ZED TESTER")
    print("  Testing STORY ZED")
    print("=" * 70)

    try:
        # Get authenticated session
        session = get_authenticated_session()

        # Create test runner
        runner = TestRunner(session, verbose=args.verbose)

        if args.persona_id:
            runner.persona_id = args.persona_id

        # Run tests
        success = runner.run_all_tests(story_filter=args.story)

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
        print(f"  Stories Created: {len(test_results['stories_created'])}")
        print(f"  Total Tests:     {test_results['total_tests']}")
        print(f"  ✅ Passed:        {test_results['passed']}")
        print(f"  ❌ Failed:        {test_results['failed']}")
        print(f"  Success Rate:    {test_results['success_rate']}")
        print(f"  Duration:        {test_results['duration_seconds']:.2f}s")
        print(f"\n  Results saved to: {RESULTS_FILE}")

        if test_results["stories_created"]:
            print("\n  Created Stories:")
            for story in test_results["stories_created"]:
                print(f"    - {story['name']}")
                print(f"      Story ID: {story['story_id']}")
                print(f"      Room ID:  {story['room_id']}")

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
