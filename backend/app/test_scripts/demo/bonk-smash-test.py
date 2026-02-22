#!/usr/bin/env python3
"""
QA Demo Composition Test Script - Story + Chat + Constant Content

This script tests the demo composition system with focus on:
- Story runtime panel with chat integration
- Constant content block that persists during interaction
- Verifying the "Required QA Story + Room + Constant Content" scenario

=============================================================================
PURPOSE
=============================================================================

This validates the core product requirement: constant top content + story
runtime + chat panel all working together in the same demo room.

Test checklist from reference:
1. Start runtime (or confirm auto-start)
2. Make one story choice
3. Send chat message
4. Verify block remains constant throughout

=============================================================================
COMPOSITION STRUCTURE
=============================================================================

    ┌─────────────────────────────────────────────────────┐
    │  [intro] Instructions (markdown, card)              │
    │  "### Test Steps..."                                │
    ├───────────────────────────┬─────────────────────────┤
    │  story                    │  chat                   │
    │  (storyRuntime)           │  (chat)                 │
    │  primary, 68%             │  auxiliary, 32%         │
    │  send_events_to_chat      │  participant mode       │
    └───────────────────────────┴─────────────────────────┘

=============================================================================
USAGE
=============================================================================

Basic usage:
    python test_qa_demo_story_chat.py

With custom story:
    python test_qa_demo_story_chat.py --story-id YOUR-UUID

Custom panel sizes:
    python test_qa_demo_story_chat.py --story-size 75 --chat-size 25

List/inspect existing demos:
    python test_qa_demo_story_chat.py --list
    python test_qa_demo_story_chat.py --get SLUG

=============================================================================
"""

import argparse
import json
import random
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# =============================================================================
# PATH SETUP
# =============================================================================

sys.path.insert(0, str(Path(__file__).parent.parent))
from auth_helper import get_authenticated_session, AuthenticationError

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_STORY_ID = "172109da-8b5f-48f2-9e7a-4259657691dc"
SLUG_PREFIX = "qa-story-chat"


# =============================================================================
# UTILITIES
# =============================================================================

def generate_slug(prefix: str = SLUG_PREFIX) -> str:
    """Generate a unique slug: {prefix}-{MMDD}-{HHMM}-{random4}"""
    timestamp = datetime.now().strftime("%m%d-%H%M")
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{prefix}-{timestamp}-{suffix}"


def generate_results_filename(slug: str) -> str:
    """Generate results filename from slug."""
    return f"test_results_{slug.replace('-', '_')}.json"


# =============================================================================
# COMPOSITION PAYLOAD
# =============================================================================

def get_story_chat_composition(
    story_id: str | None = None,
    story_panel_size: int = 68,
    chat_panel_size: int = 32,
    with_participants: bool = False,
    participant_panel_size: int = 25,
    participant_options: dict | None = None
) -> dict[str, Any]:
    """
    Build the Story + Chat + Constant Content composition.

    This composition is designed to test the integration between:
    - Story runtime (making choices, advancing narrative)
    - Chat (sending messages, receiving responses)
    - Constant content (instructions that don't change)

    Key differences from baseline:
    - Slightly different panel sizing (68/32 vs 65/35)
    - Content block with explicit test instructions
    - No min/max size constraints (tests default behavior)

    Args:
        story_id: Story UUID to bind
        story_panel_size: Story panel percentage (default 68)
        chat_panel_size: Chat panel percentage (default 32)

    Returns:
        dict: Composition payload
    """
    composition = {
        "schema_version": 1,
        "layout_mode": "panels",

        # Runtime starts automatically - we want to test immediate engagement
        "runtime_policy": "auto",

        # First available persona - simplest path
        "persona_policy": "first_available",

        # Participant mode - user can interact with both story and chat
        "chat_mode": "participant",

        # No theme overrides - test default styling
        "fixed_user_persona_id": None,
        "page_theme_id": None,
        "cards_theme_id": None,

        "panels": [
            # -----------------------------------------------------------------
            # Story Runtime Panel
            # -----------------------------------------------------------------
            {
                "id": "story",
                "kind": "storyRuntime",
                "prominence": "primary",
                "order": 1,
                "title": "Story Runtime",
                "default_size": story_panel_size,
                "min_size": 35,  # Don't let it get too small
                "viewport_mode": "panel",
                "options": {
                }
            },

            # -----------------------------------------------------------------
            # Chat Panel
            # -----------------------------------------------------------------
            {
                "id": "chat",
                "kind": "chat",
                "prominence": "auxiliary",
                "order": 2,
                "title": "Room Chat",
                "default_size": chat_panel_size,
                "min_size": 20,
                "viewport_mode": "panel",
                "options": {
                    "mode": "participant"
                }
            }
        ],

        "blocks": [
            # -----------------------------------------------------------------
            # Instructions Block (Top)
            # -----------------------------------------------------------------
            # This block contains the QA test steps.
            # It should remain visible and unchanged throughout all interactions.
            {
                "id": "intro",
                "type": "content",
                "region": "top",
                "order": 1,
                "title": "Instructions",
                "visibility": "visible",
                "content_json": {
                    "format": "markdown",
                    "value": """### Test Steps
push buttons you dummy""",
                    "metadata": {
                        "variant": "card"
                    }
                }
            }
        ],

        "metadata_json": {
            "description": "bonk smash kill fight",
            "auto_respond": True,
            "test_type": "story_chat_integration"
        }
    }

    # Add participant panel if requested
    if with_participants:
        panel_opts = {"showUsers": True, "showAgents": True, "compact": False, "allowQuickAdd": True}
        if participant_options:
            panel_opts.update(participant_options)
        composition["panels"].append({
            "id": "participants",
            "kind": "participantPanel",
            "prominence": "auxiliary",
            "order": 3,
            "title": "other crayon snorters",
            "default_size": participant_panel_size,
            "min_size": 15,
            "viewport_mode": "panel",
            "options": panel_opts
        })

    # Add story binding if provided
    if story_id:
        composition["metadata_json"]["story_id"] = story_id

    return composition


def get_demo_config_payload(slug: str, title: str | None = None) -> dict[str, Any]:
    """Build DemoConfig creation payload."""
    if title is None:
        title = "play stupid games win stupid prizes"

    return {
        "slug": slug,
        "title": title,
        "scope": "personal",
        "is_active": True,
        "default_auto_respond": True,
        "metadata_json": {
            "created_by": "test_qa_demo_story_chat.py",
            "created_at": datetime.now().isoformat(),
            "test_scenario": "bonk_smash_kill"
        }
    }


# =============================================================================
# DEMO BUILDER CLASS
# =============================================================================

class DemoBuilder:
    """Orchestrates demo composition test workflow."""

    def __init__(
        self,
        session: requests.Session,
        story_id: str | None = None,
        demo_slug: str | None = None,
        verbose: bool = False,
        story_panel_size: int = 68,
        chat_panel_size: int = 32,
        with_participants: bool = False,
        participant_panel_size: int = 25,
        participant_options: dict | None = None
    ):
        self.session = session
        self.story_id = story_id
        self.demo_slug = demo_slug or generate_slug()
        self.verbose = verbose
        self.story_panel_size = story_panel_size
        self.chat_panel_size = chat_panel_size
        self.with_participants = with_participants
        self.participant_panel_size = participant_panel_size
        self.participant_options = participant_options

        # Track created resources
        self.demo_config_id: str | None = None
        self.demo_config: dict | None = None
        self.composition_response: dict | None = None
        self.session_response: dict | None = None

        # Results tracking
        self.results = {
            "test_name": "QA Story Chat Constant Content",
            "start_time": datetime.now().isoformat(),
            "story_id": story_id,
            "demo_slug": self.demo_slug,
            "steps": [],
            "success": False,
            "errors": []
        }

    def log(self, message: str):
        print(f"  {message}")

    def debug(self, message: str):
        if self.verbose:
            print(f"  [DEBUG] {message}")

    def log_step(self, step_name: str, success: bool, details: str = ""):
        self.results["steps"].append({
            "step": step_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        status = "✓" if success else "✗"
        self.log(f"{status} {step_name}" + (f" - {details}" if details else ""))

    # =========================================================================
    # API METHODS
    # =========================================================================

    def create_demo_config(self) -> dict:
        """Create DemoConfig via POST /api/v1/demos/"""
        self.log("\n📦 Creating DemoConfig...")

        payload = get_demo_config_payload(self.demo_slug)
        self.debug(f"POST {BASE_URL}/demos/")
        self.debug(f"Payload: {json.dumps(payload, indent=2)}")

        response = self.session.post(f"{BASE_URL}/demos/", json=payload)

        if response.status_code in (200, 201):
            self.demo_config = response.json()
            self.demo_config_id = self.demo_config["id"]
            self.log_step("Create DemoConfig", True, f"id={self.demo_config_id}")
            self.debug(f"Response: {json.dumps(self.demo_config, indent=2)}")
            return self.demo_config
        else:
            error = response.json().get("detail", response.text)
            self.log_step("Create DemoConfig", False, f"{response.status_code}: {error}")
            raise Exception(f"Failed to create DemoConfig: {error}")

    def set_composition(self) -> dict:
        """Set composition via PUT /api/v1/demos/configs/{id}/composition"""
        if not self.demo_config_id:
            raise Exception("No DemoConfig created")

        self.log("\n🎨 Setting composition...")

        composition = get_story_chat_composition(
            story_id=self.story_id,
            story_panel_size=self.story_panel_size,
            chat_panel_size=self.chat_panel_size,
            with_participants=self.with_participants,
            participant_panel_size=self.participant_panel_size,
            participant_options=self.participant_options
        )

        self.debug(f"PUT {BASE_URL}/demos/configs/{self.demo_config_id}/composition")
        self.debug(f"Composition: {json.dumps(composition, indent=2)}")

        response = self.session.put(
            f"{BASE_URL}/demos/configs/{self.demo_config_id}/composition",
            json=composition
        )

        if response.status_code in (200, 201):
            self.composition_response = response.json()
            panels = len(composition.get("panels", []))
            blocks = len(composition.get("blocks", []))
            self.log_step("Set Composition", True, f"{panels} panels, {blocks} blocks")
            return self.composition_response
        else:
            error = response.json().get("detail", response.text)
            self.log_step("Set Composition", False, f"{response.status_code}: {error}")
            raise Exception(f"Failed to set composition: {error}")

    def create_session(self) -> dict:
        """Create session via POST /api/v1/demos/{slug}/session"""
        self.log("\n🚀 Creating demo session...")

        response = self.session.post(f"{BASE_URL}/demos/{self.demo_slug}/session")

        if response.status_code in (200, 201):
            self.session_response = response.json()
            session_id = self.session_response.get("session_id", "N/A")
            has_runtime = "runtime" in self.session_response
            self.log_step("Create Session", True, f"session={session_id[:8]}..., runtime={has_runtime}")
            return self.session_response
        else:
            error = response.json().get("detail", response.text)
            self.log_step("Create Session", False, f"{response.status_code}: {error}")
            raise Exception(f"Failed to create session: {error}")

    def list_demos(self, limit: int = 20) -> list[dict]:
        """List existing demos."""
        self.log("\n📋 Listing demo configs...")
        response = self.session.get(f"{BASE_URL}/demos/", params={"limit": limit})
        if response.status_code == 200:
            data = response.json()
            demos = data.get("data", [])
            self.log(f"  Found {len(demos)} demo(s)")
            return demos
        return []

    def get_demo_by_slug(self, slug: str) -> dict | None:
        """Get demo by slug."""
        self.log(f"\n🔍 Getting demo: {slug}")
        response = self.session.get(f"{BASE_URL}/demos/{slug}")
        if response.status_code == 200:
            return response.json()
        return None

    def delete_demo(self, demo_config_id: str) -> bool:
        """Delete a demo config."""
        self.log(f"\n🗑️ Deleting DemoConfig {demo_config_id}...")
        response = self.session.delete(f"{BASE_URL}/demos/configs/{demo_config_id}")
        if response.status_code in (200, 204):
            self.log_step("Delete DemoConfig", True)
            return True
        self.log_step("Delete DemoConfig", False, f"HTTP {response.status_code}")
        return False

    # =========================================================================
    # WORKFLOW
    # =========================================================================

    def run_full_workflow(self, skip_session: bool = False) -> bool:
        """Execute complete demo creation workflow."""
        try:
            self.create_demo_config()
            self.set_composition()
            if not skip_session:
                self.create_session()
            self.results["success"] = True
            return True
        except Exception as e:
            self.results["errors"].append(str(e))
            self.results["success"] = False
            raise


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test QA Demo - Story + Chat + Constant Content",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Story options
    story_group = parser.add_mutually_exclusive_group()
    story_group.add_argument("--story-id", type=str, default=DEFAULT_STORY_ID)
    story_group.add_argument("--no-story", action="store_true")

    # Demo options
    parser.add_argument("--slug", type=str, default=None)
    parser.add_argument("--story-size", type=int, default=68)
    parser.add_argument("--chat-size", type=int, default=32)
    parser.add_argument("--with-participants", action="store_true",
        help="Add a participant panel showing room users and agents")
    parser.add_argument("--participant-size", type=int, default=25)
    parser.add_argument("--participant-options", type=str, default=None,
        help='JSON options for participantPanel')

    # Workflow options
    parser.add_argument("--no-session", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true")

    # Inspection options
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--get", type=str, metavar="SLUG")

    # Cleanup
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--demo-config-id", type=str)

    args = parser.parse_args()

    story_id = None if args.no_story else args.story_id

    # Parse participant options
    participant_options = None
    if args.participant_options:
        try:
            participant_options = json.loads(args.participant_options)
        except json.JSONDecodeError as e:
            print(f"\n❌ Invalid JSON for --participant-options: {e}")
            return 1

    # Dry run
    if args.dry_run:
        slug = args.slug or generate_slug()
        comp = get_story_chat_composition(
            story_id, args.story_size, args.chat_size,
            args.with_participants, args.participant_size, participant_options
        )
        print("\n" + "=" * 70)
        print("  DRY RUN - Story + Chat + Constant Content")
        print("=" * 70)
        print(f"\n  Slug: {slug}")
        print(f"  Story: {story_id or 'None'}")
        print(f"  Sizes: Story={args.story_size}%, Chat={args.chat_size}%")
        if args.with_participants:
            print(f"  Participants: {args.participant_size}%")
        print("\n  Composition:")
        print(json.dumps(comp, indent=2))
        return 0

    print("\n" + "=" * 70)
    print("  QA DEMO TEST - STORY + CHAT + CONSTANT CONTENT")
    print("=" * 70)

    try:
        print("\n🔐 Authenticating...")
        session = get_authenticated_session()
        print("  ✓ Authentication successful")

        builder = DemoBuilder(
            session=session,
            story_id=story_id,
            demo_slug=args.slug,
            verbose=args.verbose,
            story_panel_size=args.story_size,
            chat_panel_size=args.chat_size,
            with_participants=args.with_participants,
            participant_panel_size=args.participant_size,
            participant_options=participant_options
        )

        # List mode
        if args.list:
            demos = builder.list_demos()
            if demos:
                print("\n  Existing demos:")
                for d in demos:
                    print(f"    {d.get('slug', 'N/A'):<35} {d.get('id', 'N/A')}")
            return 0

        # Get mode
        if args.get:
            demo = builder.get_demo_by_slug(args.get)
            if demo:
                print(f"\n  Demo: {args.get}")
                print(f"  ID: {demo.get('id')}")
                print(json.dumps(demo, indent=2) if args.json else "")
            return 0 if demo else 1

        # Cleanup mode
        if args.cleanup:
            if not args.demo_config_id:
                print("\n❌ --cleanup requires --demo-config-id")
                return 1
            return 0 if builder.delete_demo(args.demo_config_id) else 1

        # Create mode
        builder.run_full_workflow(skip_session=args.no_session)

        print("\n" + "=" * 70)
        print("  TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n  Demo Config ID: {builder.demo_config_id}")
        print(f"  Demo Slug: {builder.demo_slug}")
        print(f"  Story ID: {story_id or 'None'}")
        print(f"\n  🌐 http://localhost:5173/demo/{builder.demo_slug}")

        # Save results
        results_file = generate_results_filename(builder.demo_slug)
        builder.results["end_time"] = datetime.now().isoformat()
        with open(results_file, "w") as f:
            json.dump(builder.results, f, indent=2)
        print(f"\n  📄 Results: {results_file}")

        print(f"\n  🧹 Cleanup: python {Path(__file__).name} --cleanup --demo-config-id {builder.demo_config_id}")
        print("\n" + "=" * 70 + "\n")

        return 0

    except AuthenticationError as e:
        print(f"\n❌ Auth failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
