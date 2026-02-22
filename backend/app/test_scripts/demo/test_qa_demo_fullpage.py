#!/usr/bin/env python3
"""
QA Demo Composition Test Script - Page-Sized Panel

This script tests the demo composition system with focus on:
- Full viewport panel behavior (viewport_mode: "page")
- Single-panel layout taking over the entire workspace
- Canvas panel type

=============================================================================
PURPOSE
=============================================================================

This validates the page-sized panel feature where a single panel can
consume the entire viewport, hiding split-panel chrome.

Key characteristics:
- Only ONE panel can have viewport_mode="page"
- The panel takes over the full workspace
- Split panel UI is minimized/hidden
- Good for immersive experiences (canvas, full-screen story)

Use cases:
- Canvas/whiteboard applications
- Immersive story experiences
- Full-screen presentations
- Drawing/design tools

=============================================================================
COMPOSITION STRUCTURE
=============================================================================

    ┌─────────────────────────────────────────────────────┐
    │                                                     │
    │                    canvas-full                      │
    │                    (canvas)                         │
    │                                                     │
    │              viewport_mode: "page"                  │
    │           (consumes full workspace)                 │
    │                                                     │
    │                                                     │
    └─────────────────────────────────────────────────────┘

=============================================================================
USAGE
=============================================================================

Basic usage:
    python test_qa_demo_fullpage.py

Different panel kind:
    python test_qa_demo_fullpage.py --panel-kind storyRuntime
    python test_qa_demo_fullpage.py --panel-kind chat

With story (for storyRuntime kind):
    python test_qa_demo_fullpage.py --panel-kind storyRuntime --story-id UUID

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
SLUG_PREFIX = "qa-fullpage"

# Valid panel kinds for full-page mode
VALID_PANEL_KINDS = ["canvas", "storyRuntime", "chat", "content", "storyPlayer", "storyEditor"]


def generate_slug(prefix: str = SLUG_PREFIX) -> str:
    timestamp = datetime.now().strftime("%m%d-%H%M")
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{prefix}-{timestamp}-{suffix}"


def generate_results_filename(slug: str) -> str:
    return f"test_results_{slug.replace('-', '_')}.json"


# =============================================================================
# COMPOSITION PAYLOAD
# =============================================================================

def get_fullpage_composition(
    story_id: str | None = None,
    panel_kind: str = "canvas",
    panel_title: str | None = None,
    with_participants: bool = False,
    participant_panel_size: int = 25,
    participant_options: dict | None = None
) -> dict[str, Any]:
    """
    Build the Page-Sized Panel composition.

    This creates a single panel that takes over the full viewport.
    If with_participants is True, switches to split-panel mode instead
    of full-page mode (since full-page doesn't support multiple panels).

    Key characteristics:
    - viewport_mode: "page" - Full workspace takeover (unless with_participants)
    - Only ONE panel (the page-sized one) when in page mode
    - No blocks (they would conflict with full-page)
    - Manual runtime policy (doesn't auto-start)

    Args:
        story_id: Story UUID (required for storyRuntime kind)
        panel_kind: Type of panel ("canvas", "storyRuntime", "chat", etc.)
        panel_title: Custom title for the panel
        with_participants: If True, use split-panel mode with participant panel
        participant_panel_size: Size for participant panel when in split mode
        participant_options: Options for participantPanel

    Returns:
        dict: Composition payload
    """

    # Determine default title based on kind
    if panel_title is None:
        panel_title = {
            "canvas": "Canvas",
            "storyRuntime": "Story",
            "chat": "Chat",
            "content": "Content",
            "storyPlayer": "Story Player",
            "storyEditor": "Story Editor"
        }.get(panel_kind, panel_kind.title())

    # Build panel options based on kind
    panel_options = {}
    if panel_kind == "storyRuntime":
        panel_options = {
            "send_runtime_events_to_chat": False,  # No chat panel
            "viewer_mode": False
        }
    elif panel_kind == "chat":
        panel_options = {
            "mode": "participant",
            "include_internal_messages": False
        }

    composition = {
        "schema_version": 1,
        "layout_mode": "panels",

        # Manual runtime - full-page experiences often need setup first
        "runtime_policy": "manual",

        "persona_policy": "first_available",
        "chat_mode": "participant",

        "fixed_user_persona_id": None,
        "page_theme_id": None,
        "cards_theme_id": None,

        "panels": [
            # -----------------------------------------------------------------
            # Main Panel (Full-Page or Split)
            # -----------------------------------------------------------------
            {
                "id": "canvas-full",
                "kind": panel_kind,
                "prominence": "primary",
                "order": 1,
                "title": panel_title,

                # ============================================================
                # viewport_mode: "page" vs "panel"
                # ============================================================
                # "page" = Full workspace takeover (split panel chrome hidden)
                # "panel" = Standard split-panel mode (used with participants)
                "viewport_mode": "panel" if with_participants else "page",

                # Size only matters in split-panel mode
                "default_size": 75 if with_participants else None,
                "min_size": 40 if with_participants else None,

                "options": panel_options if panel_options else {}
            }
        ],

        # No blocks - they would conflict with full-page takeover
        "blocks": [],

        "metadata_json": {
            "description": f"QA Full-page {panel_kind} demo",
            "note": "Only one panel may use viewport_mode='page'",
            "test_type": "fullpage_panel",
            "panel_kind": panel_kind
        }
    }

    # Add participant panel if requested (switches to split-panel mode)
    if with_participants:
        panel_opts = {"showUsers": True, "showAgents": True, "compact": False, "allowQuickAdd": True}
        if participant_options:
            panel_opts.update(participant_options)
        composition["panels"].append({
            "id": "participants",
            "kind": "participantPanel",
            "prominence": "auxiliary",
            "order": 2,
            "title": "Participants",
            "default_size": participant_panel_size,
            "min_size": 15,
            "viewport_mode": "panel",
            "options": panel_opts
        })
        composition["metadata_json"]["note"] = "Split-panel mode (--with-participants)"

    # Add story binding if provided
    if story_id:
        composition["metadata_json"]["story_id"] = story_id

    return composition


def get_demo_config_payload(slug: str, panel_kind: str = "canvas") -> dict[str, Any]:
    return {
        "slug": slug,
        "title": f"QA Page Sized Panel ({panel_kind})",
        "scope": "personal",
        "is_active": True,
        "default_auto_respond": False,
        "metadata_json": {
            "created_by": "test_qa_demo_fullpage.py",
            "created_at": datetime.now().isoformat(),
            "test_scenario": "page_sized_panel",
            "panel_kind": panel_kind
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
        panel_kind: str = "canvas",
        panel_title: str | None = None,
        with_participants: bool = False,
        participant_panel_size: int = 25,
        participant_options: dict | None = None
    ):
        self.session = session
        self.story_id = story_id
        self.demo_slug = demo_slug or generate_slug()
        self.verbose = verbose
        self.panel_kind = panel_kind
        self.panel_title = panel_title
        self.with_participants = with_participants
        self.participant_panel_size = participant_panel_size
        self.participant_options = participant_options

        self.demo_config_id: str | None = None
        self.demo_config: dict | None = None
        self.composition_response: dict | None = None
        self.session_response: dict | None = None

        self.results = {
            "test_name": "QA Page Sized Panel",
            "start_time": datetime.now().isoformat(),
            "story_id": story_id,
            "demo_slug": self.demo_slug,
            "panel_kind": panel_kind,
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
        payload = get_demo_config_payload(self.demo_slug, self.panel_kind)
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
        composition = get_fullpage_composition(
            story_id=self.story_id,
            panel_kind=self.panel_kind,
            panel_title=self.panel_title,
            with_participants=self.with_participants,
            participant_panel_size=self.participant_panel_size,
            participant_options=self.participant_options
        )
        self.debug(f"Composition: {json.dumps(composition, indent=2)}")

        response = self.session.put(
            f"{BASE_URL}/demos/configs/{self.demo_config_id}/composition",
            json=composition
        )
        if response.status_code in (200, 201):
            self.composition_response = response.json()
            self.log_step("Set Composition", True, f"fullpage {self.panel_kind}")
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
        description="Test QA Demo - Page-Sized Panel (Full Viewport)",
        epilog=f"Valid panel kinds: {', '.join(VALID_PANEL_KINDS)}"
    )

    parser.add_argument("--story-id", type=str, default=None,
        help="Story UUID (required for storyRuntime kind)")
    parser.add_argument("--no-story", action="store_true")

    parser.add_argument("--slug", type=str, default=None)
    parser.add_argument("--panel-kind", type=str, default="canvas",
        choices=VALID_PANEL_KINDS,
        help="Type of panel to display full-page (default: canvas)")
    parser.add_argument("--panel-title", type=str, default=None,
        help="Custom title for the panel")

    # Participant panel options
    parser.add_argument("--with-participants", action="store_true",
        help="Add participant panel (switches from page to split-panel mode)")
    parser.add_argument("--participant-size", type=int, default=25,
        help="Participant panel size percentage (default: 25)")
    parser.add_argument("--participant-options", type=str, default=None,
        help="JSON string of participant panel options (e.g., '{\"compact\": true}')")

    parser.add_argument("--no-session", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true")

    parser.add_argument("--list", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--demo-config-id", type=str)

    args = parser.parse_args()

    # Story ID logic
    story_id = None
    if not args.no_story:
        if args.story_id:
            story_id = args.story_id
        elif args.panel_kind == "storyRuntime":
            # Use default story for storyRuntime
            story_id = DEFAULT_STORY_ID

    # Parse participant options if provided
    participant_options = None
    if args.participant_options:
        try:
            participant_options = json.loads(args.participant_options)
        except json.JSONDecodeError as e:
            print(f"\n❌ Invalid JSON for --participant-options: {e}")
            return 1

    if args.dry_run:
        slug = args.slug or generate_slug()
        comp = get_fullpage_composition(
            story_id=story_id,
            panel_kind=args.panel_kind,
            panel_title=args.panel_title,
            with_participants=args.with_participants,
            participant_panel_size=args.participant_size,
            participant_options=participant_options
        )
        print("\n" + "=" * 70)
        print("  DRY RUN - Page-Sized Panel")
        print("=" * 70)
        print(f"\n  Slug: {slug}")
        print(f"  Panel Kind: {args.panel_kind}")
        viewport_mode = "panel (split)" if args.with_participants else "page (full workspace)"
        print(f"  Viewport Mode: {viewport_mode}")
        if args.with_participants:
            print(f"  Participant Panel: size={args.participant_size}%")
        print("\n  Composition:")
        print(json.dumps(comp, indent=2))
        return 0

    print("\n" + "=" * 70)
    print("  QA DEMO TEST - PAGE-SIZED PANEL")
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
            panel_kind=args.panel_kind,
            panel_title=args.panel_title,
            with_participants=args.with_participants,
            participant_panel_size=args.participant_size,
            participant_options=participant_options
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
        print(f"  Panel Kind: {args.panel_kind}")
        viewport_mode = "panel (split)" if args.with_participants else "page (full workspace)"
        print(f"  Viewport Mode: {viewport_mode}")
        if args.with_participants:
            print(f"  Participant Panel: size={args.participant_size}%")

        print(f"\n  🌐 http://localhost:5173/demo/{builder.demo_slug}")

        if args.with_participants:
            main_size = 100 - args.participant_size
            print("\n  Expected behavior (split-panel mode):")
            print("  ┌───────────────────────────────┬─────────────────────┐")
            print(f"  │  {args.panel_kind:^29}  │  participants       │")
            print(f"  │  ({main_size}%)                         │  ({args.participant_size}%)              │")
            print("  │                               │  showUsers: ✓       │")
            print("  │                               │  showAgents: ✓      │")
            print("  └───────────────────────────────┴─────────────────────┘")
        else:
            print("\n  Expected behavior:")
            print("  ┌─────────────────────────────────────────────────────┐")
            print(f"  │  {args.panel_kind:^49}  │")
            print("  │                                                     │")
            print("  │            (consumes full workspace)                │")
            print("  │         no split-panel chrome visible               │")
            print("  │                                                     │")
            print("  └─────────────────────────────────────────────────────┘")

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
