#!/usr/bin/env python3
"""
QA Demo Composition Test Script - Multiplayer/Observer Mode

This script tests the demo composition system with focus on:
- Observer chat mode (read-only)
- Participant panel display
- Manual runtime policy
- Multi-user/multiplayer scenarios

=============================================================================
PURPOSE
=============================================================================

This validates observer/spectator scenarios where users:
- Can see chat messages but not send them
- Can see who's participating
- Cannot start the runtime themselves (manual policy)

Use cases:
- Presentations where audience watches
- Moderated sessions
- Demo spectator mode

=============================================================================
COMPOSITION STRUCTURE
=============================================================================

    ┌─────────────────────────────────────────────────────┐
    │  [context] What You Are Seeing                      │
    │  "Observer mode: verify multiple humans/agents..."  │
    ├───────────────────────────────┬─────────────────────┤
    │  chat-main                    │  participants       │
    │  (chat)                       │  (participantPanel) │
    │  primary, 70%                 │  auxiliary, 30%     │
    │  observer mode                │  shows who's in room│
    │  include_internal_messages    │                     │
    └───────────────────────────────┴─────────────────────┘

=============================================================================
USAGE
=============================================================================

Basic usage:
    python test_qa_demo_observer.py

With story (optional for observer mode):
    python test_qa_demo_observer.py --story-id YOUR-UUID

Custom panel sizes:
    python test_qa_demo_observer.py --chat-size 60 --participant-size 40

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

sys.path.insert(0, str(Path(__file__).parent.parent))
from auth_helper import get_authenticated_session, AuthenticationError

BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_STORY_ID = "172109da-8b5f-48f2-9e7a-4259657691dc"
SLUG_PREFIX = "qa-observer"


def generate_slug(prefix: str = SLUG_PREFIX) -> str:
    timestamp = datetime.now().strftime("%m%d-%H%M")
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{prefix}-{timestamp}-{suffix}"


def generate_results_filename(slug: str) -> str:
    return f"test_results_{slug.replace('-', '_')}.json"


# =============================================================================
# COMPOSITION PAYLOAD
# =============================================================================

def get_observer_composition(
    story_id: str | None = None,
    chat_panel_size: int = 70,
    participant_panel_size: int = 30
) -> dict[str, Any]:
    """
    Build the Multiplayer/Observer composition.

    Key characteristics:
    - chat_mode: "observer" - Users cannot send messages
    - runtime_policy: "manual" - Only owner can start
    - participantPanel - Shows who's in the room
    - include_internal_messages: true - Show system/agent messages

    This is a chat-focused layout where the conversation is primary
    and participants are shown in a sidebar.

    Args:
        story_id: Optional story UUID (observer demos may not need a story)
        chat_panel_size: Chat panel percentage (default 70)
        participant_panel_size: Participant panel percentage (default 30)

    Returns:
        dict: Composition payload
    """
    composition = {
        "schema_version": 1,
        "layout_mode": "panels",

        # =====================================================================
        # KEY: Manual runtime policy
        # =====================================================================
        # Only the demo owner can start the runtime.
        # Observers wait for the presenter to initiate.
        "runtime_policy": "manual",

        "persona_policy": "first_available",

        # =====================================================================
        # KEY: Observer chat mode
        # =====================================================================
        # Users can read messages but cannot send them.
        # This is the default for all chat panels in this composition.
        "chat_mode": "observer",

        "fixed_user_persona_id": None,
        "page_theme_id": None,
        "cards_theme_id": None,

        "panels": [
            # -----------------------------------------------------------------
            # Chat Panel (Primary) - Observer Mode
            # -----------------------------------------------------------------
            {
                "id": "chat-main",
                "kind": "chat",
                "prominence": "primary",
                "order": 1,
                "title": "Conversation",
                "default_size": chat_panel_size,
                "min_size": 35,
                "viewport_mode": "panel",
                "options": {
                    # Explicit observer mode at panel level
                    "mode": "observer",

                    # KEY: Show internal/system messages
                    # In observer mode, users often want to see everything
                    # including agent thinking, system events, etc.
                    "include_internal_messages": True
                }
            },

            # -----------------------------------------------------------------
            # Participant Panel (Auxiliary)
            # -----------------------------------------------------------------
            # Shows who is in the room: humans, agents, personas.
            # Useful for understanding who's speaking in the chat.
            {
                "id": "participants",
                "kind": "participantPanel",
                "prominence": "auxiliary",
                "order": 2,
                "title": "Participants",
                "default_size": participant_panel_size,
                "viewport_mode": "panel"
                # participantPanel typically doesn't need options
            }
        ],

        "blocks": [
            # -----------------------------------------------------------------
            # Context Block - Explains Observer Mode
            # -----------------------------------------------------------------
            {
                "id": "context",
                "type": "context",
                "region": "top",
                "order": 1,
                "title": "What You Are Seeing",
                "visibility": "visible",
                "content_json": {
                    "format": "markdown",
                    "value": """**Observer Mode Active**

You are viewing this demo as an observer. You can see:
- All chat messages (including internal/system messages)
- Who is participating in the room

You cannot:
- Send messages
- Start the story runtime
- Make choices

This mode is for watching presentations and demonstrations.""",
                    "metadata": {
                        "variant": "card"
                    }
                }
            }
        ],

        "metadata_json": {
            "description": "QA Observer/Multiplayer demo",
            # Auto-respond is off - this is a controlled presentation
            "auto_respond": False,
            "test_type": "observer_mode"
        }
    }

    # Story is optional for observer demos
    if story_id:
        composition["metadata_json"]["story_id"] = story_id

    return composition


def get_demo_config_payload(slug: str) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": "QA Multiplayer Observer",
        "scope": "personal",
        "is_active": True,
        # Auto-respond OFF for observer mode
        "default_auto_respond": False,
        "metadata_json": {
            "created_by": "test_qa_demo_observer.py",
            "created_at": datetime.now().isoformat(),
            "test_scenario": "multiplayer_observer"
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
        chat_panel_size: int = 70,
        participant_panel_size: int = 30
    ):
        self.session = session
        self.story_id = story_id
        self.demo_slug = demo_slug or generate_slug()
        self.verbose = verbose
        self.chat_panel_size = chat_panel_size
        self.participant_panel_size = participant_panel_size

        self.demo_config_id: str | None = None
        self.demo_config: dict | None = None
        self.composition_response: dict | None = None
        self.session_response: dict | None = None

        self.results = {
            "test_name": "QA Multiplayer Observer",
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
            "step": step_name, "success": success,
            "details": details, "timestamp": datetime.now().isoformat()
        })
        status = "✓" if success else "✗"
        self.log(f"{status} {step_name}" + (f" - {details}" if details else ""))

    def create_demo_config(self) -> dict:
        self.log("\n📦 Creating DemoConfig...")
        payload = get_demo_config_payload(self.demo_slug)
        self.debug(f"Payload: {json.dumps(payload, indent=2)}")

        response = self.session.post(f"{BASE_URL}/demos/", json=payload)
        if response.status_code in (200, 201):
            self.demo_config = response.json()
            self.demo_config_id = self.demo_config["id"]
            self.log_step("Create DemoConfig", True, f"id={self.demo_config_id}")
            return self.demo_config
        else:
            error = response.json().get("detail", response.text)
            self.log_step("Create DemoConfig", False, str(error))
            raise Exception(f"Failed: {error}")

    def set_composition(self) -> dict:
        if not self.demo_config_id:
            raise Exception("No DemoConfig created")

        self.log("\n🎨 Setting composition...")
        composition = get_observer_composition(
            story_id=self.story_id,
            chat_panel_size=self.chat_panel_size,
            participant_panel_size=self.participant_panel_size
        )
        self.debug(f"Composition: {json.dumps(composition, indent=2)}")

        response = self.session.put(
            f"{BASE_URL}/demos/configs/{self.demo_config_id}/composition",
            json=composition
        )
        if response.status_code in (200, 201):
            self.composition_response = response.json()
            self.log_step("Set Composition", True, "observer mode, manual runtime")
            return self.composition_response
        else:
            error = response.json().get("detail", response.text)
            self.log_step("Set Composition", False, str(error))
            raise Exception(f"Failed: {error}")

    def create_session(self) -> dict:
        self.log("\n🚀 Creating demo session...")
        response = self.session.post(f"{BASE_URL}/demos/{self.demo_slug}/session")
        if response.status_code in (200, 201):
            self.session_response = response.json()
            session_id = self.session_response.get("session_id", "N/A")
            self.log_step("Create Session", True, f"session={session_id[:8]}...")
            return self.session_response
        else:
            error = response.json().get("detail", response.text)
            self.log_step("Create Session", False, str(error))
            raise Exception(f"Failed: {error}")

    def list_demos(self, limit: int = 20) -> list[dict]:
        response = self.session.get(f"{BASE_URL}/demos/", params={"limit": limit})
        if response.status_code == 200:
            return response.json().get("data", [])
        return []

    def delete_demo(self, demo_config_id: str) -> bool:
        self.log(f"\n🗑️ Deleting {demo_config_id}...")
        response = self.session.delete(f"{BASE_URL}/demos/configs/{demo_config_id}")
        success = response.status_code in (200, 204)
        self.log_step("Delete DemoConfig", success)
        return success

    def run_full_workflow(self, skip_session: bool = False) -> bool:
        try:
            self.create_demo_config()
            self.set_composition()
            if not skip_session:
                self.create_session()
            self.results["success"] = True
            return True
        except Exception as e:
            self.results["errors"].append(str(e))
            raise


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test QA Demo - Multiplayer/Observer Mode"
    )

    story_group = parser.add_mutually_exclusive_group()
    story_group.add_argument("--story-id", type=str, default=None,
        help="Optional story UUID (observer demos may not need a story)")
    story_group.add_argument("--no-story", action="store_true")

    parser.add_argument("--slug", type=str, default=None)
    parser.add_argument("--chat-size", type=int, default=70)
    parser.add_argument("--participant-size", type=int, default=30)

    parser.add_argument("--no-session", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true")

    parser.add_argument("--list", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--demo-config-id", type=str)

    args = parser.parse_args()

    story_id = None if args.no_story else args.story_id

    if args.dry_run:
        slug = args.slug or generate_slug()
        comp = get_observer_composition(story_id, args.chat_size, args.participant_size)
        print("\n" + "=" * 70)
        print("  DRY RUN - Observer Mode")
        print("=" * 70)
        print(f"\n  Slug: {slug}")
        print(f"  Mode: Observer (read-only chat)")
        print(f"  Runtime: Manual (owner starts)")
        print("\n  Composition:")
        print(json.dumps(comp, indent=2))
        return 0

    print("\n" + "=" * 70)
    print("  QA DEMO TEST - MULTIPLAYER/OBSERVER MODE")
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
            chat_panel_size=args.chat_size,
            participant_panel_size=args.participant_size
        )

        if args.list:
            demos = builder.list_demos()
            print("\n  Existing demos:")
            for d in demos:
                print(f"    {d.get('slug', 'N/A'):<35} {d.get('id', 'N/A')}")
            return 0

        if args.cleanup:
            if not args.demo_config_id:
                print("\n❌ --cleanup requires --demo-config-id")
                return 1
            return 0 if builder.delete_demo(args.demo_config_id) else 1

        builder.run_full_workflow(skip_session=args.no_session)

        print("\n" + "=" * 70)
        print("  TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n  Demo Config ID: {builder.demo_config_id}")
        print(f"  Demo Slug: {builder.demo_slug}")
        print(f"  Chat Mode: observer (read-only)")
        print(f"  Runtime Policy: manual (owner starts)")
        print(f"\n  🌐 http://localhost:5173/demo/{builder.demo_slug}")

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
