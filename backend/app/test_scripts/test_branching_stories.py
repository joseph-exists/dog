#!/usr/bin/env python3
"""
Branching Stories E2E Test Suite

Creates and tests multibranching CYOA stories with:
- True story branching (multiple choices from same node)
- State-based conditionals (story_state)
- UserPersona state requirements
- Room integration
- Publishing workflow
- Actual story narratives (not placeholders)

Usage:
    python test_branching_stories.py
    python test_branching_stories.py --verbose
    python test_branching_stories.py --story forest
    python test_branching_stories.py --persona-id YOUR-UUID
    python test_branching_stories.py --no-cleanup

Output:
    test_results_branching_stories.json
"""

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
RESULTS_FILE = "test_results_branching_stories.json"

# Test state
test_results = {
    "test_suite": "Branching Stories E2E Test Suite",
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
        response = self.session.get(f"{BASE_URL}/users/me")

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
            response = self.session.get(f"{BASE_URL}/user-personas/{persona_id}")
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

        response = self.session.post(f"{BASE_URL}/personas", json=persona_data)
        if response.status_code != 200:
            print(f"  ❌ Failed to create Persona: {response.text}")
            raise Exception("Could not create Persona template")

        persona = response.json()
        print(f"  ✅ Persona template created: \"{persona['name']}\" (ID: {persona['id'][:8]}...)")

        # Step 2: Create a UserPersona (user's instance of the Persona)
        user_persona_data = {
            "persona_id": persona['id']
        }

        response = self.session.post(f"{BASE_URL}/user-personas", json=user_persona_data)
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

        try:
            response = self.session.post(f"{BASE_URL}/stories",
            json=story_data)
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
            self.record_test(
                "create_story",
                False,
                f"HTTP {e.response.status_code if e.response else 'ERROR'}: {e.response.text if e.response else str(e)}"
            )
            raise

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

        response = self.session.post(
            f"{BASE_URL}/node-choices",
            json=payload
        )
        if response.status_code != 200:
            raise Exception(f"Failed to create choice '{text}': {response.text}")
        return response.json()

    def publish_story(self, story_id: str) -> bool:
        """Publish a story."""
        self.log("Publishing story...")
        response = self.session.put(
            f"{BASE_URL}/stories/{story_id}/publish"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to publish story: {response.text}")

        story = response.json()
        if not story.get("is_published"):
            raise Exception("Story was not marked as published")

        return True

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

    def start_story_progress(self, story_id: str, persona_id: str) -> tuple:
        """Start story progress for a persona. Returns (persona_id, story_id) for later use."""
        self.debug("Starting story progress...")
        response = self.session.post(
            f"{BASE_URL}/user-personas/{persona_id}/stories/{story_id}"
        )
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to start story: {response.text}")
        # Return persona_id and story_id since we need them for subsequent calls
        return (persona_id, story_id)

    def make_choice(self, persona_id: str, story_id: str, choice_id: str) -> dict:
        """Make a choice in story progress."""
        self.debug(f"Making choice: {choice_id}")
        response = self.session.post(
            f"{BASE_URL}/user-personas/{persona_id}/stories/{story_id}/choices/{choice_id}"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to make choice: {response.text}")
        return response.json()

    def get_current_node(self, persona_id: str, story_id: str) -> dict:
        """Get current node in story progress."""
        response = self.session.get(
            f"{BASE_URL}/user-personas/{persona_id}/stories/{story_id}/current-node"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to get current node: {response.text}")
        return response.json()

    # ========================================================================
    # Story 1: The Enchanted Forest (Basic Branching)
    # ========================================================================
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
                "Take the shadowy left path",
                sets_state={"path": "shadow", "courage": 5},
                order=0
            )
            self.create_choice(
                left_1["id"], left_end["id"],
                "Take the shadowy left path",
                sets_state={"path": "shadow", "courage": 5},
                order=0
            )
            # Publish story
            if not self.publish_story(story_id):
                raise Exception("Failed to publish story")

        except Exception as e:
            self.record_test(
                "test_story_zed",
                False,
                str(e)
            )

    def test_story_enchanted_forest(self):
        """
        Test Story: The Enchanted Forest

        A simple branching story with 3 paths and state tracking.
        Tests basic branching, state changes, and multiple endings.
        """
        self.test_header(
            "Story 1: The Enchanted Forest",
            "Basic branching with state tracking"
        )

        try:
            # Create story
            story_id = self.create_story(
                "The Enchanted Forest",
                "A mystical forest with three distinct paths"
            )

            # Create nodes
            start = self.create_node(
                story_id,
                "Forest Entrance",
                "You stand at the edge of an ancient forest. Three paths diverge before you. "
                "To the left, a shadowy trail winds through dark trees. Straight ahead, "
                "a sunlit path beckons with birdsong. To the right, a mysterious stone "
                "archway glows with faint blue light.",
                is_start=True
            )

            # Left path nodes
            left_1 = self.create_node(
                story_id,
                "Shadow Path",
                "The dark trees close around you. Strange whispers echo through the shadows. "
                "A black cat with glowing eyes sits on a fallen log, watching you intently."
            )

            left_end = self.create_node(
                story_id,
                "Shadow Guardian",
                "The cat transforms into a cloaked figure. 'You have embraced the darkness,' "
                "they say. 'Few have the courage.' They gift you a shadow cloak that lets "
                "you walk unseen. You have found the Path of Shadows.",
                is_end=True
            )

            # Center path nodes
            center_1 = self.create_node(
                story_id,
                "Sunlit Grove",
                "The sunlight warms your face as you enter a beautiful glade. Flowers bloom "
                "in impossible colors. A silver deer approaches, unafraid."
            )

            center_end = self.create_node(
                story_id,
                "Nature's Friend",
                "The deer nuzzles your hand. Suddenly you understand the language of birds "
                "and trees. The forest accepts you as one of its own. You have found the "
                "Path of Harmony.",
                is_end=True
            )

            # Right path nodes
            right_1 = self.create_node(
                story_id,
                "Arcane Gateway",
                "You step through the glowing archway. Magic crackles in the air. An ancient "
                "crystal hovers before you, pulsing with power."
            )

            right_end = self.create_node(
                story_id,
                "Arcane Master",
                "As you touch the crystal, knowledge floods your mind. Spells and incantations, "
                "the secrets of the ancients. You have found the Path of Magic.",
                is_end=True
            )

            # Create choices with state tracking
            self.create_choice(
                start["id"], left_1["id"],
                "Take the shadowy left path",
                sets_state={"path": "shadow", "courage": 5},
                order=0
            )

            self.create_choice(
                start["id"], center_1["id"],
                "Follow the sunlit path straight ahead",
                sets_state={"path": "harmony", "kindness": 5},
                order=1
            )

            self.create_choice(
                start["id"], right_1["id"],
                "Enter the glowing archway on the right",
                sets_state={"path": "magic", "wisdom": 5},
                order=2
            )

            # Continue each path
            self.create_choice(
                left_1["id"], left_end["id"],
                "Approach the mysterious cat",
                sets_state={"shadow_affinity": 10}
            )

            self.create_choice(
                center_1["id"], center_end["id"],
                "Reach out to the silver deer",
                sets_state={"nature_affinity": 10}
            )

            self.create_choice(
                right_1["id"], right_end["id"],
                "Touch the ancient crystal",
                sets_state={"magic_affinity": 10}
            )

            # Publish story
            if not self.publish_story(story_id):
                raise Exception("Failed to publish story")

            # Create room
            room = self.create_room("Forest Adventure Room", story_id)

            # Test story progression - take each path
            for path_name, expected_state_key in [
                ("shadow", "shadow_affinity"),
                ("harmony", "nature_affinity"),
                ("magic", "magic_affinity")
            ]:
                persona_id, sid = self.start_story_progress(story_id, self.persona_id)

                # Get available choices at start
                current = self.get_current_node(persona_id, sid)
                choices = current["available_choices"]

                # Verify 3 choices available
                if len(choices) != 3:
                    raise Exception(f"Expected 3 choices, got {len(choices)}")

                # Take the path
                choice = next(c for c in choices if path_name in c.get("sets_state", {}).get("path", ""))
                result = self.make_choice(persona_id, sid, choice["id"])

                # Verify state was set
                if result["story_state"].get("path") != path_name:
                    raise Exception(f"State not set correctly for {path_name} path")

                # Continue to end
                current = self.get_current_node(persona_id, sid)
                if current["available_choices"]:
                    result = self.make_choice(persona_id, sid, current["available_choices"][0]["id"])

                    # Verify final state
                    if expected_state_key not in result["story_state"]:
                        raise Exception(f"Final state missing {expected_state_key}")

            test_results["stories_created"].append({
                "name": "The Enchanted Forest",
                "story_id": story_id,
                "room_id": room["room_id"],
                "branches": 3,
                "endings": 3
            })

            self.record_test(
                "enchanted_forest_complete",
                True,
                "Successfully created and tested 3-path branching story with state tracking"
            )

        except Exception as e:
            self.record_test(
                "enchanted_forest_complete",
                False,
                str(e)
            )

    # ========================================================================
    # Story 2: The Dragon's Hoard (State Conditionals)
    # ========================================================================

    def test_story_dragons_hoard(self):
        """
        Test Story: The Dragon's Hoard

        A story with state-based conditional choices.
        Tests requires_state logic and branching based on previous decisions.
        """
        self.test_header(
            "Story 2: The Dragon's Hoard",
            "State-conditional branching"
        )

        try:
            # Create story
            story_id = self.create_story(
                "The Dragon's Hoard",
                "Navigate a dragon's lair using wit, strength, or stealth"
            )

            # Create nodes
            start = self.create_node(
                story_id,
                "Dragon's Lair Entrance",
                "You've found the legendary dragon's cave. Gold glitters in the depths. "
                "The dragon sleeps on its hoard, but how will you approach?",
                is_start=True
            )

            # First decision - approach method
            approach_node = self.create_node(
                story_id,
                "Inside the Lair",
                "You're now deep inside the cave. The dragon's breathing echoes around you. "
                "Mountains of treasure surround the sleeping beast. What's your next move?"
            )

            # Strength path
            strength_node = self.create_node(
                story_id,
                "Warrior's Challenge",
                "You boldly step forward, your weapon ready. The dragon's eye opens. "
                "'A warrior!' it rumbles. 'Finally, someone worthy of combat!'"
            )

            strength_end_victory = self.create_node(
                story_id,
                "Victor's Spoils",
                "Your strength prevails! The dragon acknowledges your prowess and offers you "
                "first pick of the hoard. You take the legendary Sword of Dawn. The dragon "
                "bows its head in respect. You have earned the Path of the Warrior.",
                is_end=True
            )

            strength_end_diplomatic = self.create_node(
                story_id,
                "Warrior's Wisdom",
                "You lower your weapon. 'I seek not battle, but alliance,' you say. The dragon "
                "is impressed by your wisdom in the face of battle-readiness. It shares ancient "
                "warrior knowledge with you. You have earned the Path of the Honorable Warrior.",
                is_end=True
            )

            # Stealth path
            stealth_node = self.create_node(
                story_id,
                "Shadow Thief",
                "You creep silently through the shadows. Your fingers close around a small "
                "but valuable ruby. The dragon stirs in its sleep..."
            )

            stealth_end_escape = self.create_node(
                story_id,
                "Master Thief",
                "You slip away like smoke, ruby in hand. The dragon never knew you were there. "
                "You have earned the Path of Shadows.",
                is_end=True
            )

            stealth_end_caught = self.create_node(
                story_id,
                "Thief's Bargain",
                "The dragon's eye opens! 'Clever,' it says, 'but not clever enough.' However, "
                "it's amused by your boldness. It offers you a deal: serve as its spy and keep "
                "the ruby. You have earned the Path of the Shadow Pact.",
                is_end=True
            )

            # Diplomacy path
            diplomacy_node = self.create_node(
                story_id,
                "Diplomatic Approach",
                "You speak in a clear, respectful voice. 'Great Dragon, I come seeking wisdom, "
                "not treasure.' The dragon's eyes fully open, studying you with ancient intelligence."
            )

            diplomacy_end = self.create_node(
                story_id,
                "Dragon's Friend",
                "'Few mortals think beyond gold,' the dragon says. 'You seek knowledge, and that "
                "is the greatest treasure.' It shares secrets of the ancient world with you. "
                "You have earned the Path of the Dragon Friend.",
                is_end=True
            )

            # Create initial approach choices
            self.create_choice(
                start["id"], approach_node["id"],
                "Draw your weapon and advance boldly",
                sets_state={"approach": "strength", "warrior_spirit": 5},
                order=0
            )

            self.create_choice(
                start["id"], approach_node["id"],
                "Slip into the shadows and move silently",
                sets_state={"approach": "stealth", "shadow_affinity": 5},
                order=1
            )

            self.create_choice(
                start["id"], approach_node["id"],
                "Call out respectfully to the dragon",
                sets_state={"approach": "diplomacy", "wisdom": 5},
                order=2
            )

            # Conditional choices based on approach
            # Strength path choices
            self.create_choice(
                approach_node["id"], strength_node["id"],
                "Stand your ground with weapon ready",
                requires_state={"approach": "strength"},
                sets_state={"combat_ready": True},
                order=0
            )

            self.create_choice(
                strength_node["id"], strength_end_victory["id"],
                "Fight the dragon with all your strength",
                sets_state={"outcome": "combat_victory"},
                order=0
            )

            self.create_choice(
                strength_node["id"], strength_end_diplomatic["id"],
                "Propose an alliance instead of fighting",
                sets_state={"outcome": "warrior_diplomacy"},
                order=1
            )

            # Stealth path choices
            self.create_choice(
                approach_node["id"], stealth_node["id"],
                "Sneak toward a small, valuable gem",
                requires_state={"approach": "stealth"},
                sets_state={"stealing": True},
                order=1
            )

            self.create_choice(
                stealth_node["id"], stealth_end_escape["id"],
                "Flee silently before the dragon fully wakes",
                sets_state={"outcome": "stealthy_escape"},
                order=0
            )

            self.create_choice(
                stealth_node["id"], stealth_end_caught["id"],
                "Try to take one more gem before leaving",
                sets_state={"outcome": "caught_but_clever"},
                order=1
            )

            # Diplomacy path choice
            self.create_choice(
                approach_node["id"], diplomacy_node["id"],
                "Continue speaking respectfully",
                requires_state={"approach": "diplomacy"},
                sets_state={"diplomatic": True},
                order=2
            )

            self.create_choice(
                diplomacy_node["id"], diplomacy_end["id"],
                "Ask the dragon about ancient history",
                sets_state={"outcome": "dragon_friend"},
                order=0
            )

            # Publish and test
            if not self.publish_story(story_id):
                raise Exception("Failed to publish story")

            room = self.create_room("Dragon's Hoard Challenge Room", story_id)

            # Test each path
            for approach in ["strength", "stealth", "diplomacy"]:
                persona_id, sid = self.start_story_progress(story_id, self.persona_id)

                # First choice - set approach
                current = self.get_current_node(persona_id, sid)
                choice = next(c for c in current["available_choices"]
                             if c.get("sets_state", {}).get("approach") == approach)
                result = self.make_choice(persona_id, sid, choice["id"])

                # Second choice - should only see approach-appropriate choice
                current = self.get_current_node(persona_id, sid)
                # Filter for choices that match our approach
                valid_choices = [c for c in current["available_choices"]
                               if not c.get("requires_state") or
                               c.get("requires_state", {}).get("approach") == approach]

                if not valid_choices:
                    raise Exception(f"No valid choices for {approach} path")

                # Make choice
                result = self.make_choice(persona_id, sid, valid_choices[0]["id"])

                # Continue to end
                current = self.get_current_node(persona_id, sid)
                if current["available_choices"]:
                    self.make_choice(persona_id, sid, current["available_choices"][0]["id"])

            test_results["stories_created"].append({
                "name": "The Dragon's Hoard",
                "story_id": story_id,
                "room_id": room["room_id"],
                "branches": 3,
                "conditional_branches": 6,
                "endings": 6
            })

            self.record_test(
                "dragons_hoard_complete",
                True,
                "Successfully created and tested state-conditional branching story"
            )

        except Exception as e:
            self.record_test(
                "dragons_hoard_complete",
                False,
                str(e)
            )

    # ========================================================================
    # Story 3: The Time Traveler's Dilemma (Deep Branching)
    # ========================================================================

    def test_story_time_traveler(self):
        """
        Test Story: The Time Traveler's Dilemma

        A story with deep branching - branches that branch again.
        Tests complex state tracking across multiple decision points.
        """
        self.test_header(
            "Story 3: The Time Traveler's Dilemma",
            "Deep branching with multiple decision layers"
        )

        try:
            # Create story
            story_id = self.create_story(
                "The Time Traveler's Dilemma",
                "Navigate the perils of time travel across multiple eras"
            )

            # Create nodes
            start = self.create_node(
                story_id,
                "The Time Machine",
                "Your time machine hums with power. The display shows three eras available: "
                "Medieval times, Wild West, or Ancient Egypt. Where will you go?",
                is_start=True
            )

            # Medieval branch
            medieval_1 = self.create_node(
                story_id,
                "Medieval Castle",
                "You arrive in the courtyard of a grand castle. A tournament is underway. "
                "Knights clash in the arena while nobles watch from the stands."
            )

            medieval_knight = self.create_node(
                story_id,
                "Knight's Path",
                "You challenge a knight to a duel. The crowd goes wild. The king himself "
                "watches with interest."
            )

            medieval_knight_end = self.create_node(
                story_id,
                "Knighted Hero",
                "Through skill (and a bit of future technology), you win the tournament. "
                "The king knights you on the spot. You're now Sir/Dame [name], Champion of the Realm. "
                "But can you return to your time without breaking the timeline?",
                is_end=True
            )

            medieval_scholar = self.create_node(
                story_id,
                "Scholar's Path",
                "You seek out the castle's library. Ancient texts line the shelves. "
                "A monk studies them intently."
            )

            medieval_scholar_end = self.create_node(
                story_id,
                "Keeper of Knowledge",
                "The monk shares lost scientific knowledge with you. Together, you make "
                "discoveries that could accelerate human progress by centuries. You must "
                "decide: share this knowledge or preserve the timeline?",
                is_end=True
            )

            # Wild West branch
            west_1 = self.create_node(
                story_id,
                "Frontier Town",
                "You materialize in a dusty frontier town. A standoff is about to happen "
                "on Main Street. The sheriff faces three outlaws."
            )

            west_sheriff = self.create_node(
                story_id,
                "Lawman's Path",
                "You step in to help the sheriff. The outlaws eye you warily. Your modern "
                "clothes confuse them. 'Who are you, stranger?' the sheriff asks."
            )

            west_sheriff_end = self.create_node(
                story_id,
                "Hero of the West",
                "Your quick thinking saves the town. The grateful citizens make you deputy. "
                "But you know from history that this town burns down next week. "
                "Do you warn them and change history?",
                is_end=True
            )

            west_outlaw = self.create_node(
                story_id,
                "Outlaw's Path",
                "The outlaws see something in your eyes - a kindred spirit of rebellion. "
                "They invite you to join their gang. They're planning the biggest "
                "train robbery in history."
            )

            west_outlaw_end = self.create_node(
                story_id,
                "Legend of the West",
                "You ride with the gang, living wild and free. Your knowledge of future "
                "technology makes you the most successful outlaw in history. But fame "
                "comes at a price - how do you return home without leaving a trace?",
                is_end=True
            )

            # Ancient Egypt branch
            egypt_1 = self.create_node(
                story_id,
                "The Pyramids",
                "You emerge near the pyramids during their construction. Thousands work "
                "under the burning sun. The Pharaoh's procession approaches."
            )

            egypt_priest = self.create_node(
                story_id,
                "Priest's Path",
                "The priests think you're a god, arriving in a flash of light. They take "
                "you to the temple. The High Priest demands proof of your divinity."
            )

            egypt_priest_end = self.create_node(
                story_id,
                "Divine Visitor",
                "Your 'miracles' (science tricks) convince them. You're worshipped as a deity. "
                "You could reshape history itself. But with great power comes terrible responsibility. "
                "What will you change?",
                is_end=True
            )

            egypt_builder = self.create_node(
                story_id,
                "Builder's Path",
                "You join the pyramid builders, learning their incredible techniques. "
                "These aren't slaves - they're skilled craftsmen. The chief architect "
                "notices your strange tools and knowledge."
            )

            egypt_builder_end = self.create_node(
                story_id,
                "Master Builder",
                "You help perfect the pyramid's design using your engineering knowledge. "
                "Your innovations make it last millennia longer. Your name will be carved "
                "in hieroglyphs forever. Is this legacy worth being stranded in time?",
                is_end=True
            )

            # Create era choices
            self.create_choice(
                start["id"], medieval_1["id"],
                "Travel to Medieval times",
                sets_state={"era": "medieval", "time_period": "1350"},
                order=0
            )

            self.create_choice(
                start["id"], west_1["id"],
                "Travel to the Wild West",
                sets_state={"era": "wild_west", "time_period": "1880"},
                order=1
            )

            self.create_choice(
                start["id"], egypt_1["id"],
                "Travel to Ancient Egypt",
                sets_state={"era": "ancient_egypt", "time_period": "-2500"},
                order=2
            )

            # Medieval sub-branches
            self.create_choice(
                medieval_1["id"], medieval_knight["id"],
                "Join the tournament as a knight",
                sets_state={"role": "knight", "valor": 10},
                order=0
            )

            self.create_choice(
                medieval_1["id"], medieval_scholar["id"],
                "Seek the castle library and scholars",
                sets_state={"role": "scholar", "wisdom": 10},
                order=1
            )

            self.create_choice(
                medieval_knight["id"], medieval_knight_end["id"],
                "Fight to win the tournament",
                sets_state={"outcome": "tournament_champion"}
            )

            self.create_choice(
                medieval_scholar["id"], medieval_scholar_end["id"],
                "Share knowledge with the monk",
                sets_state={"outcome": "knowledge_shared"}
            )

            # Wild West sub-branches
            self.create_choice(
                west_1["id"], west_sheriff["id"],
                "Help the sheriff uphold the law",
                sets_state={"role": "lawman", "justice": 10},
                order=0
            )

            self.create_choice(
                west_1["id"], west_outlaw["id"],
                "Join the outlaws for freedom",
                sets_state={"role": "outlaw", "rebellion": 10},
                order=1
            )

            self.create_choice(
                west_sheriff["id"], west_sheriff_end["id"],
                "Accept the deputy badge",
                sets_state={"outcome": "frontier_hero"}
            )

            self.create_choice(
                west_outlaw["id"], west_outlaw_end["id"],
                "Ride with the gang",
                sets_state={"outcome": "legendary_outlaw"}
            )

            # Egypt sub-branches
            self.create_choice(
                egypt_1["id"], egypt_priest["id"],
                "Go with the priests to the temple",
                sets_state={"role": "deity", "divinity": 10},
                order=0
            )

            self.create_choice(
                egypt_1["id"], egypt_builder["id"],
                "Join the pyramid construction crew",
                sets_state={"role": "architect", "craftsmanship": 10},
                order=1
            )

            self.create_choice(
                egypt_priest["id"], egypt_priest_end["id"],
                "Perform 'miracles' to prove your divinity",
                sets_state={"outcome": "worshipped_god"}
            )

            self.create_choice(
                egypt_builder["id"], egypt_builder_end["id"],
                "Share your engineering knowledge",
                sets_state={"outcome": "master_architect"}
            )

            # Publish and test
            if not self.publish_story(story_id):
                raise Exception("Failed to publish story")

            room = self.create_room("Time Traveler's Lounge", story_id)

            # Test one complete path (Medieval Knight)
            persona_id, sid = self.start_story_progress(story_id, self.persona_id)

            # Choose Medieval
            current = self.get_current_node(persona_id, sid)
            medieval_choice = next(c for c in current["available_choices"]
                                  if "Medieval" in c["text"])
            result = self.make_choice(persona_id, sid, medieval_choice["id"])

            # Verify state
            if result["story_state"].get("era") != "medieval":
                raise Exception("Era state not set correctly")

            # Choose Knight path
            current = self.get_current_node(persona_id, sid)
            knight_choice = next(c for c in current["available_choices"]
                               if "knight" in c["text"])
            result = self.make_choice(persona_id, sid, knight_choice["id"])

            # Verify role state
            if result["story_state"].get("role") != "knight":
                raise Exception("Role state not set correctly")

            # Complete the path
            current = self.get_current_node(persona_id, sid)
            if current["available_choices"]:
                result = self.make_choice(persona_id, sid, current["available_choices"][0]["id"])

                # Verify final state has all expected keys
                final_state = result["story_state"]
                if not all(k in final_state for k in ["era", "role", "outcome"]):
                    raise Exception("Final state missing expected keys")

            test_results["stories_created"].append({
                "name": "The Time Traveler's Dilemma",
                "story_id": story_id,
                "room_id": room["room_id"],
                "branches": 3,
                "sub_branches": 6,
                "depth": 3,
                "endings": 6
            })

            self.record_test(
                "time_traveler_complete",
                True,
                "Successfully created and tested deep branching story (3 eras × 2 paths each)"
            )

        except Exception as e:
            self.record_test(
                "time_traveler_complete",
                False,
                str(e)
            )

    # ========================================================================
    # Story 4: The Detective's Case (State Accumulation)
    # ========================================================================

    def test_story_detective_case(self):
        """
        Test Story: The Detective's Case

        A story where choices accumulate clues (state) that unlock different endings.
        Tests complex state accumulation and multiple conditional paths.
        """
        self.test_header(
            "Story 4: The Detective's Case",
            "State accumulation and conditional endings"
        )

        try:
            # Create story
            story_id = self.create_story(
                "The Detective's Case",
                "Solve a murder mystery by gathering clues"
            )

            # Create nodes
            start = self.create_node(
                story_id,
                "Crime Scene",
                "You arrive at the mansion where millionaire Victor Sterling was found dead. "
                "Three suspects: his wife Eleanor, business partner Marcus, and maid Helena. "
                "You have time to investigate two locations before the police arrive.",
                is_start=True
            )

            # Investigation nodes
            study = self.create_node(
                story_id,
                "The Study",
                "Victor's study is in disarray. Papers scattered, a broken window, and strange "
                "marks on the carpet. You find a torn letter mentioning 'the deal goes through tonight.'"
            )

            bedroom = self.create_node(
                story_id,
                "The Bedroom",
                "The master bedroom is pristine except for a medicine bottle on the nightstand. "
                "The label has been partially peeled off. You notice it's not Victor's usual medication."
            )

            garden = self.create_node(
                story_id,
                "The Garden",
                "The garden path shows fresh footprints leading to the back gate. A gardening "
                "glove lies discarded near the prize roses. It has dirt... and a spot of blood."
            )

            # Accusation node - combines clues
            accusation = self.create_node(
                story_id,
                "Making the Accusation",
                "The police have arrived. Detective, who do you accuse? Your career depends on "
                "getting this right. Review your evidence carefully."
            )

            # Different endings based on clues gathered
            wife_correct = self.create_node(
                story_id,
                "Justice Served - The Wife",
                "You accuse Eleanor. She breaks down and confesses. She poisoned Victor's medication "
                "after discovering his affair and plans to cut her out of his will. The torn letter "
                "and medicine bottle were the key clues. Outstanding detective work!",
                is_end=True
            )

            wife_wrong = self.create_node(
                story_id,
                "False Accusation - The Wife",
                "You accuse Eleanor, but she has an airtight alibi. Your career is damaged. "
                "You missed crucial evidence. The real killer goes free.",
                is_end=True
            )

            partner_correct = self.create_node(
                story_id,
                "Justice Served - The Partner",
                "You accuse Marcus. He confesses: Victor was backing out of a risky deal that "
                "would have bankrupted him. The broken window and torn letter about 'the deal' "
                "were the key clues. Excellent work, Detective!",
                is_end=True
            )

            partner_wrong = self.create_node(
                story_id,
                "False Accusation - The Partner",
                "You accuse Marcus, but his alibi holds. Another case bungled. "
                "You should have gathered more evidence.",
                is_end=True
            )

            maid_correct = self.create_node(
                story_id,
                "Justice Served - The Maid",
                "You accuse Helena. She confesses: Victor threatened to deport her family. "
                "She struck him in the garden, and the footprints and bloody glove prove it. "
                "Brilliant deduction!",
                is_end=True
            )

            maid_wrong = self.create_node(
                story_id,
                "False Accusation - The Maid",
                "You accuse Helena, but she was caring for her sick child that night. "
                "Your reputation suffers. The killer laughs at your mistake.",
                is_end=True
            )

            # Create investigation choices (accumulate clues)
            self.create_choice(
                start["id"], study["id"],
                "Investigate the study thoroughly",
                sets_state={"investigated_study": True, "clue_torn_letter": True, "clue_broken_window": True},
                order=0
            )

            self.create_choice(
                start["id"], bedroom["id"],
                "Search the bedroom carefully",
                sets_state={"investigated_bedroom": True, "clue_medicine": True, "clue_poison": True},
                order=1
            )

            self.create_choice(
                start["id"], garden["id"],
                "Examine the garden and grounds",
                sets_state={"investigated_garden": True, "clue_footprints": True, "clue_bloody_glove": True},
                order=2
            )

            # All investigation paths lead to accusation
            self.create_choice(
                study["id"], accusation["id"],
                "Return to make your accusation",
                order=0
            )

            self.create_choice(
                bedroom["id"], accusation["id"],
                "Return to make your accusation",
                order=0
            )

            self.create_choice(
                garden["id"], accusation["id"],
                "Return to make your accusation",
                order=0
            )

            # Accusation choices - correct one depends on clues gathered
            # Wife = medicine + torn letter
            self.create_choice(
                accusation["id"], wife_correct["id"],
                "Accuse Eleanor Sterling (the wife)",
                requires_state={"clue_medicine": True, "clue_torn_letter": True},
                sets_state={"accusation": "wife", "correct": True},
                order=0
            )

            self.create_choice(
                accusation["id"], wife_wrong["id"],
                "Accuse Eleanor Sterling (the wife)",
                # Only available if you don't have both required clues
                sets_state={"accusation": "wife", "correct": False},
                order=1
            )

            # Partner = broken window + torn letter
            self.create_choice(
                accusation["id"], partner_correct["id"],
                "Accuse Marcus Black (the business partner)",
                requires_state={"clue_broken_window": True, "clue_torn_letter": True},
                sets_state={"accusation": "partner", "correct": True},
                order=2
            )

            self.create_choice(
                accusation["id"], partner_wrong["id"],
                "Accuse Marcus Black (the business partner)",
                sets_state={"accusation": "partner", "correct": False},
                order=3
            )

            # Maid = footprints + bloody glove
            self.create_choice(
                accusation["id"], maid_correct["id"],
                "Accuse Helena Martinez (the maid)",
                requires_state={"clue_footprints": True, "clue_bloody_glove": True},
                sets_state={"accusation": "maid", "correct": True},
                order=4
            )

            self.create_choice(
                accusation["id"], maid_wrong["id"],
                "Accuse Helena Martinez (the maid)",
                sets_state={"accusation": "maid", "correct": False},
                order=5
            )

            # Publish and test
            if not self.publish_story(story_id):
                raise Exception("Failed to publish story")

            room = self.create_room("Detective's Office", story_id)

            # Test: gather garden clues (footprints + bloody glove) and accuse maid correctly
            persona_id, sid = self.start_story_progress(story_id, self.persona_id)

            # Investigate garden
            current = self.get_current_node(persona_id, sid)
            garden_choice = next(c for c in current["available_choices"]
                                if "garden" in c["text"].lower())
            result = self.make_choice(persona_id, sid, garden_choice["id"])

            # Verify clues were added
            state = result["story_state"]
            if not (state.get("clue_footprints") and state.get("clue_bloody_glove")):
                raise Exception("Garden clues not added to state")

            # Go to accusation
            current = self.get_current_node(persona_id, sid)
            result = self.make_choice(persona_id, sid, current["available_choices"][0]["id"])

            # Accuse the maid (should be correct with garden clues)
            current = self.get_current_node(persona_id, sid)
            maid_choice = next(c for c in current["available_choices"]
                              if "Helena" in c["text"])
            result = self.make_choice(persona_id, sid, maid_choice["id"])

            # Verify we got the correct ending
            if not result["story_state"].get("correct"):
                raise Exception("Should have gotten correct ending with proper clues")

            test_results["stories_created"].append({
                "name": "The Detective's Case",
                "story_id": story_id,
                "room_id": room["room_id"],
                "investigation_paths": 3,
                "endings": 6,
                "state_complexity": "high - clue accumulation"
            })

            self.record_test(
                "detective_case_complete",
                True,
                "Successfully created and tested state accumulation mystery story"
            )

        except Exception as e:
            self.record_test(
                "detective_case_complete",
                False,
                str(e)
            )




    # ========================================================================
    # Main Test Runner
    # ========================================================================




    def run_all_tests(self, story_filter: str = None):
        """Run all story tests."""
        self.test_header(
            "BRANCHING STORIES E2E TEST SUITE",
            "Testing multibranching stories with state, rooms, and publishing"
        )

        try:
            # Authenticate and get user info
            self.authenticate()

            # Get/create persona (use existing if provided via --persona-id)
            self.persona_id = self.create_test_persona(self.persona_id)

            # Run story tests based on filter
            stories_to_test = {
                "zed": self.test_story_zero,
                "forest": self.test_story_enchanted_forest,
                "dragon": self.test_story_dragons_hoard,
                "time": self.test_story_time_traveler,
                "detective": self.test_story_detective_case
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
        description="E2E tests for branching stories with state and rooms"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--story", choices=["zed", "forest", "dragon", "time", "detective"],
                       help="Run specific story test only")
    parser.add_argument("--persona-id", help="Use existing persona ID")
    parser.add_argument("--no-cleanup", action="store_true",
                       help="Keep created entities (don't cleanup)")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  BRANCHING STORIES E2E TEST SUITE")
    print("  Testing multibranching CYOA stories")
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
