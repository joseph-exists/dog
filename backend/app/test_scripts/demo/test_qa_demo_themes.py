#!/usr/bin/env python3
"""
QA Demo Composition Test Script - Theme Overrides

This script tests the demo composition system with focus on:
- Composition-level theme bindings (page_theme_id, cards_theme_id)
- Panel-level theme overrides (theme_id per panel)
- Block-level theme overrides (theme_id per block)
- Presentation JSON customization

=============================================================================
PURPOSE
=============================================================================

This validates the theme layering system where themes cascade:
1. Page theme (composition.page_theme_id) - Affects overall page
2. Cards theme (composition.cards_theme_id) - Affects card-style components
3. Panel theme (panel.theme_id) - Overrides for specific panel
4. Block theme (block.theme_id) - Overrides for specific block

Themes are referenced by UUID and must exist in the database.

=============================================================================
COMPOSITION STRUCTURE
=============================================================================

    ┌─────────────────────────────────────────────────────┐
    │  [context] Theme Override Example (block theme)     │
    ├───────────────────────────┬─────────────────────────┤
    │  story                    │  chat                   │
    │  (storyRuntime)           │  (chat)                 │
    │  panel theme override     │  (uses composition)     │
    │  chrome: minimal          │                         │
    └───────────────────────────┴─────────────────────────┘

    composition.page_theme_id = (page-level theme)
    composition.cards_theme_id = (cards-level theme)

=============================================================================
USAGE
=============================================================================

Basic usage (with placeholder UUIDs - replace with real theme IDs):
    python test_qa_demo_themes.py

With real theme UUIDs:
    python test_qa_demo_themes.py \\
        --page-theme UUID \\
        --cards-theme UUID \\
        --story-panel-theme UUID \\
        --context-block-theme UUID

List available themes first:
    python test_qa_demo_themes.py --list-themes

Skip theme validation (use placeholder UUIDs for testing):
    python test_qa_demo_themes.py --skip-theme-validation

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
SLUG_PREFIX = "qa-themes"
DEFAULT_STORY_PANEL_SIZE = 70
DEFAULT_CHAT_PANEL_SIZE = 30

# Placeholder UUIDs (these won't work unless themes exist)
# Replace with real theme UUIDs from your database
PLACEHOLDER_PAGE_THEME = "11111111-1111-1111-1111-111111111111"
PLACEHOLDER_CARDS_THEME = "22222222-2222-2222-2222-222222222222"
PLACEHOLDER_PANEL_THEME = "33333333-3333-3333-3333-333333333333"
PLACEHOLDER_BLOCK_THEME = "44444444-4444-4444-4444-444444444444"


def generate_slug(prefix: str = SLUG_PREFIX) -> str:
    timestamp = datetime.now().strftime("%m%d-%H%M")
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{prefix}-{timestamp}-{suffix}"


def generate_results_filename(slug: str) -> str:
    return f"test_results_{slug.replace('-', '_')}.json"


# =============================================================================
# COMPOSITION PAYLOAD
# =============================================================================

def get_themed_composition(
    story_id: str | None = None,
    page_theme_id: str | None = None,
    cards_theme_id: str | None = None,
    story_panel_theme_id: str | None = None,
    context_block_theme_id: str | None = None,
    story_panel_size: int = DEFAULT_STORY_PANEL_SIZE,
    chat_panel_size: int = DEFAULT_CHAT_PANEL_SIZE,
    with_participants: bool = False,
    participant_panel_size: int = 20,
    participant_options: dict | None = None
) -> dict[str, Any]:
    """
    Build a composition with theme overrides at multiple levels.

    Theme cascade order:
    1. page_theme_id - Applied to entire page/demo
    2. cards_theme_id - Applied to card-styled components
    3. panel.theme_id - Overrides for specific panel
    4. block.theme_id - Overrides for specific block

    More specific themes override less specific ones.

    Args:
        story_id: Story UUID to bind
        page_theme_id: Page-level theme UUID
        cards_theme_id: Cards-level theme UUID
        story_panel_theme_id: Theme override for story panel
        context_block_theme_id: Theme override for context block
        story_panel_size: Story panel percentage
        chat_panel_size: Chat panel percentage
        with_participants: If True, add participant panel
        participant_panel_size: Size for participant panel
        participant_options: Options for participantPanel (showUsers, showAgents, etc.)

    Returns:
        dict: Composition payload with theme bindings
    """
    composition = {
        "schema_version": 1,
        "layout_mode": "panels",
        "runtime_policy": "auto",
        "persona_policy": "first_available",
        "chat_mode": "participant",
        "fixed_user_persona_id": None,

        # =====================================================================
        # COMPOSITION-LEVEL THEMES
        # =====================================================================
        # These apply to the entire demo unless overridden by panel/block themes
        "page_theme_id": page_theme_id,
        "cards_theme_id": cards_theme_id,

        "panels": [
            # -----------------------------------------------------------------
            # Story Panel WITH Theme Override
            # -----------------------------------------------------------------
            {
                "id": "story",
                "kind": "storyRuntime",
                "prominence": "primary",
                "order": 1,
                "title": "Story (Custom Theme)",
                "default_size": story_panel_size,
                "min_size": 30,
                "max_size": 85,
                "viewport_mode": "panel",

                # ============================================================
                # PANEL-LEVEL THEME OVERRIDE
                # ============================================================
                # This theme overrides the composition-level page_theme
                # for this specific panel only
                "theme_id": story_panel_theme_id,

                # ============================================================
                # PRESENTATION JSON
                # ============================================================
                # Panel-specific presentation hints
                # These are passed to the frontend renderer
                "presentation_json": {
                    # "minimal" chrome reduces visual decorations
                    "chrome": "minimal"
                },

                "options": {
                    "send_runtime_events_to_chat": True,
                    "viewer_mode": False
                }
            },

            # -----------------------------------------------------------------
            # Chat Panel WITHOUT Theme Override
            # -----------------------------------------------------------------
            # This panel uses the composition-level themes
            {
                "id": "chat",
                "kind": "chat",
                "prominence": "auxiliary",
                "order": 2,
                "title": "Chat (Default Theme)",
                "default_size": chat_panel_size,
                "min_size": 20,
                "max_size": 50,
                "viewport_mode": "panel",
                # No theme_id - uses composition defaults
                "options": {
                    "mode": "participant"
                }
            }
        ],

        "blocks": [
            # -----------------------------------------------------------------
            # Context Block WITH Theme Override
            # -----------------------------------------------------------------
            {
                "id": "context",
                "type": "content",
                "region": "top",
                "order": 1,
                "title": "Theme Override Example",
                "visibility": "visible",

                # ============================================================
                # BLOCK-LEVEL THEME OVERRIDE
                # ============================================================
                # This theme overrides composition-level themes for this block
                "theme_id": context_block_theme_id,

                # ============================================================
                # BLOCK PRESENTATION JSON
                # ============================================================
                "presentation_json": {
                    "density": "comfortable"
                },

                "content_json": {
                    "format": "markdown",
                    "value": """### Theme Cascade Test

This block demonstrates theme layering:

| Level | Theme ID | Status |
|-------|----------|--------|
| Page | `page_theme_id` | {} |
| Cards | `cards_theme_id` | {} |
| Story Panel | `panel.theme_id` | {} |
| This Block | `block.theme_id` | {} |

Check that visual styling reflects the theme cascade.""".format(
    "Set" if page_theme_id else "Not set",
    "Set" if cards_theme_id else "Not set",
    "Set" if story_panel_theme_id else "Not set",
    "Set" if context_block_theme_id else "Not set"
),
                    "metadata": {
                        "variant": "card"
                    }
                }
            }
        ],

        "metadata_json": {
            "description": "QA Theme override test",
            "auto_respond": True,
            "test_type": "theme_layering",
            "themes_configured": {
                "page": page_theme_id is not None,
                "cards": cards_theme_id is not None,
                "story_panel": story_panel_theme_id is not None,
                "context_block": context_block_theme_id is not None
            }
        }
    }

    if story_id:
        composition["metadata_json"]["story_id"] = story_id

    # Add participant panel if requested
    if with_participants:
        panel_opts = {
            "showUsers": True,
            "showAgents": True,
            "compact": False,
            "allowQuickAdd": True
        }
        if participant_options:
            panel_opts.update(participant_options)

        composition["panels"].append({
            "id": "participants",
            "kind": "participantPanel",
            "prominence": "auxiliary",
            "order": 3,
            "title": "Participants",
            "default_size": participant_panel_size,
            "min_size": 15,
            "max_size": 35,
            "viewport_mode": "panel",
            "options": panel_opts
        })
        composition["metadata_json"]["with_participants"] = True

    return composition


def get_demo_config_payload(slug: str) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": "QA Theme Overrides",
        "scope": "personal",
        "is_active": True,
        "default_auto_respond": True,
        "metadata_json": {
            "created_by": "test_qa_demo_themes.py",
            "created_at": datetime.now().isoformat(),
            "test_scenario": "theme_overrides"
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
        page_theme_id: str | None = None,
        cards_theme_id: str | None = None,
        story_panel_theme_id: str | None = None,
        context_block_theme_id: str | None = None,
        story_panel_size: int = DEFAULT_STORY_PANEL_SIZE,
        chat_panel_size: int = DEFAULT_CHAT_PANEL_SIZE,
        with_participants: bool = False,
        participant_panel_size: int = 20,
        participant_options: dict | None = None
    ):
        self.session = session
        self.story_id = story_id
        self.demo_slug = demo_slug or generate_slug()
        self.verbose = verbose

        self.page_theme_id = page_theme_id
        self.cards_theme_id = cards_theme_id
        self.story_panel_theme_id = story_panel_theme_id
        self.context_block_theme_id = context_block_theme_id
        self.story_panel_size = story_panel_size
        self.chat_panel_size = chat_panel_size
        self.with_participants = with_participants
        self.participant_panel_size = participant_panel_size
        self.participant_options = participant_options

        self.demo_config_id: str | None = None
        self.demo_config: dict | None = None
        self.composition_response: dict | None = None
        self.session_response: dict | None = None

        self.results = {
            "test_name": "QA Theme Overrides",
            "start_time": datetime.now().isoformat(),
            "story_id": story_id,
            "demo_slug": self.demo_slug,
            "themes": {
                "page": page_theme_id,
                "cards": cards_theme_id,
                "story_panel": story_panel_theme_id,
                "context_block": context_block_theme_id
            },
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

    def list_themes(self) -> list[dict]:
        """List available themes from the API."""
        self.log("\n🎨 Listing available themes...")

        # Try common theme endpoints
        for endpoint in ["/themes", "/themes/", "/api/v1/themes"]:
            try:
                response = self.session.get(f"http://localhost:8000{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "data" in data:
                        return data["data"]
            except Exception:
                pass

        self.log("  ⚠️ Could not fetch themes (endpoint may not exist)")
        return []

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

        self.log("\n🎨 Setting composition with theme overrides...")
        composition = get_themed_composition(
            story_id=self.story_id,
            page_theme_id=self.page_theme_id,
            cards_theme_id=self.cards_theme_id,
            story_panel_theme_id=self.story_panel_theme_id,
            context_block_theme_id=self.context_block_theme_id,
            story_panel_size=self.story_panel_size,
            chat_panel_size=self.chat_panel_size,
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
            theme_count = sum([
                self.page_theme_id is not None,
                self.cards_theme_id is not None,
                self.story_panel_theme_id is not None,
                self.context_block_theme_id is not None
            ])
            self.log_step("Set Composition", True, f"{theme_count} theme(s) configured")
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
        description="Test QA Demo - Theme Overrides",
        epilog="""
Note: Theme UUIDs must reference existing themes in the database.
Use --list-themes to see available themes, or --skip-theme-validation
to test with placeholder UUIDs (composition creation will succeed but
themes won't apply).
        """
    )

    parser.add_argument("--story-id", type=str, default=DEFAULT_STORY_ID)
    parser.add_argument("--no-story", action="store_true")

    parser.add_argument("--slug", type=str, default=None)
    parser.add_argument("--story-size", type=int, default=DEFAULT_STORY_PANEL_SIZE)
    parser.add_argument("--chat-size", type=int, default=DEFAULT_CHAT_PANEL_SIZE)

    # Theme options
    parser.add_argument("--page-theme", type=str, default=None,
        help="Page-level theme UUID")
    parser.add_argument("--cards-theme", type=str, default=None,
        help="Cards-level theme UUID")
    parser.add_argument("--story-panel-theme", type=str, default=None,
        help="Story panel theme override UUID")
    parser.add_argument("--context-block-theme", type=str, default=None,
        help="Context block theme override UUID")
    parser.add_argument("--skip-theme-validation", action="store_true",
        help="Use placeholder UUIDs (themes won't actually apply)")

    # Participant panel options
    parser.add_argument("--with-participants", action="store_true",
        help="Add participant panel showing users and agents")
    parser.add_argument("--participant-size", type=int, default=20,
        help="Participant panel size percentage (default: 20)")
    parser.add_argument("--participant-options", type=str, default=None,
        help="JSON string of participant panel options (e.g., '{\"compact\": true}')")

    parser.add_argument("--no-session", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true")

    parser.add_argument("--list", action="store_true")
    parser.add_argument("--list-themes", action="store_true",
        help="List available themes and exit")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--demo-config-id", type=str)

    args = parser.parse_args()

    story_id = None if args.no_story else args.story_id

    # Theme IDs - use provided or placeholders if skip-validation
    page_theme = args.page_theme
    cards_theme = args.cards_theme
    story_panel_theme = args.story_panel_theme
    context_block_theme = args.context_block_theme

    if args.skip_theme_validation:
        page_theme = page_theme or PLACEHOLDER_PAGE_THEME
        cards_theme = cards_theme or PLACEHOLDER_CARDS_THEME
        story_panel_theme = story_panel_theme or PLACEHOLDER_PANEL_THEME
        context_block_theme = context_block_theme or PLACEHOLDER_BLOCK_THEME

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
        comp = get_themed_composition(
            story_id=story_id,
            page_theme_id=page_theme,
            cards_theme_id=cards_theme,
            story_panel_theme_id=story_panel_theme,
            context_block_theme_id=context_block_theme,
            story_panel_size=args.story_size,
            chat_panel_size=args.chat_size,
            with_participants=args.with_participants,
            participant_panel_size=args.participant_size,
            participant_options=participant_options
        )
        print("\n" + "=" * 70)
        print("  DRY RUN - Theme Overrides")
        print("=" * 70)
        print(f"\n  Slug: {slug}")
        print(f"\n  Theme Configuration:")
        print(f"    Page:          {page_theme or 'Not set'}")
        print(f"    Cards:         {cards_theme or 'Not set'}")
        print(f"    Story Panel:   {story_panel_theme or 'Not set'}")
        print(f"    Context Block: {context_block_theme or 'Not set'}")
        if args.with_participants:
            print(f"\n  Participant Panel: size={args.participant_size}%")
        print("\n  Composition:")
        print(json.dumps(comp, indent=2))
        return 0

    print("\n" + "=" * 70)
    print("  QA DEMO TEST - THEME OVERRIDES")
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
            page_theme_id=page_theme,
            cards_theme_id=cards_theme,
            story_panel_theme_id=story_panel_theme,
            context_block_theme_id=context_block_theme,
            story_panel_size=args.story_size,
            chat_panel_size=args.chat_size,
            with_participants=args.with_participants,
            participant_panel_size=args.participant_size,
            participant_options=participant_options
        )

        if args.list_themes:
            themes = builder.list_themes()
            if themes:
                print("\n  Available themes:")
                print("  " + "-" * 60)
                for t in themes:
                    tid = t.get("id", "N/A")
                    name = t.get("name", t.get("title", "Unnamed"))
                    print(f"    {tid}  {name}")
                print("  " + "-" * 60)
            else:
                print("\n  No themes found or themes endpoint not available")
            return 0

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

        print(f"\n  Theme Configuration:")
        print(f"    Page:          {page_theme or 'Not set'}")
        print(f"    Cards:         {cards_theme or 'Not set'}")
        print(f"    Story Panel:   {story_panel_theme or 'Not set'}")
        print(f"    Context Block: {context_block_theme or 'Not set'}")
        if args.with_participants:
            print(f"\n  Participant Panel: size={args.participant_size}%")

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
