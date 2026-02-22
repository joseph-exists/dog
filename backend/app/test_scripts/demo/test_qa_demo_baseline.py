#!/usr/bin/env python3
"""
QA Demo Composition Test Script - Baseline Template

This script tests the demo composition system by creating a baseline demo configuration
with panels (StoryRuntime + Chat) and a constant content block. It validates the full
workflow described in the qa-demo-composition-reference.md document.

=============================================================================
PURPOSE AND CONTEXT
=============================================================================

Demo compositions define the layout and behavior of demo pages. A composition includes:
- **Panels**: The main interactive areas (chat, storyRuntime, participantPanel, etc.)
- **Blocks**: Static or semi-static content regions (context, instructions, etc.)
- **Policies**: How the demo behaves (runtime_policy, persona_policy, chat_mode)

This script creates a "Baseline Template" demo that demonstrates:
1. Two-panel layout (Story + Chat) with configurable sizing
2. A constant top content block that persists during interactions
3. Story binding via metadata_json.story_id
4. Runtime auto-start behavior

=============================================================================
API ENDPOINTS TESTED
=============================================================================

1. POST /api/v1/demos/
   - Creates a new DemoConfig with slug, title, scope, and settings
   - Returns: { id, slug, owner_id, ... }

2. PUT /api/v1/demos/configs/{demo_config_id}/composition
   - Replaces the full composition for a demo config
   - Input: DemoPageComposition JSON (panels, blocks, policies, themes)
   - Returns: Updated DemoConfig with composition attached

3. POST /api/v1/demos/{slug}/session
   - Creates or retrieves an active demo session
   - Resolves composition, story, room, and runtime contexts
   - Returns: { session_id, composition, room, runtime, ... }

=============================================================================
COMPOSITION SCHEMA OVERVIEW
=============================================================================

The DemoPageComposition contract includes:

TOP-LEVEL FIELDS:
  - schema_version: number (currently 1)
  - layout_mode: "panels" | "tabs"
  - runtime_policy: "auto" | "manual" | "owner_only"
  - persona_policy: "first_available" | "fixed_user_persona" | "manual_prompt"
  - chat_mode: "participant" | "observer"
  - page_theme_id / cards_theme_id: Optional UUID for theming
  - panels: Array of DemoPanelSpec
  - blocks: Array of DemoBlockSpec
  - metadata_json: Free-form object (can include story_id)

PANEL FIELDS:
  - id: Unique identifier within composition
  - kind: "chat" | "storyRuntime" | "participantPanel" | "content" | "canvas" | etc.
  - prominence: "primary" | "auxiliary"
  - order: Sort order (integer >= 1)
  - default_size / min_size / max_size: Panel sizing (1-100)
  - viewport_mode: "panel" | "page" (only one panel can be "page")
  - options: Kind-specific settings (e.g., chat mode, runtime events)

BLOCK FIELDS:
  - id: Unique identifier within composition
  - type: "context" | "content" | "story" | "agentRoster" | etc.
  - region: "top" | "primary" | "auxiliary" | "footer"
  - content_json: { format: "markdown"|"json"|..., value: "...", metadata: {...} }

=============================================================================
USAGE
=============================================================================

Basic usage (auto-generates unique slug, uses default story_id):
    python test_qa_demo_baseline.py

With custom story:
    python test_qa_demo_baseline.py --story-id YOUR-UUID-HERE

Without story binding (chat-only demo):
    python test_qa_demo_baseline.py --no-story

Explicit slug (no auto-generation):
    python test_qa_demo_baseline.py --slug my-custom-demo

Custom panel sizes:
    python test_qa_demo_baseline.py --story-size 70 --chat-size 30

Verbose output with all API responses:
    python test_qa_demo_baseline.py --verbose

Dry run (show what would be created):
    python test_qa_demo_baseline.py --dry-run

List existing demos:
    python test_qa_demo_baseline.py --list

Get info about existing demo:
    python test_qa_demo_baseline.py --get qa-baseline-template

Skip session creation (composition only):
    python test_qa_demo_baseline.py --no-session

JSON output (for scripting):
    python test_qa_demo_baseline.py --json

Cleanup (delete created demo):
    python test_qa_demo_baseline.py --cleanup --demo-config-id UUID

=============================================================================
EXPECTED RESULTS
=============================================================================

After successful execution:
1. A new DemoConfig is created with the specified slug
2. The composition is attached with two panels and one block
3. A session is created/retrieved for the demo
4. The demo is accessible at: http://localhost:5173/demo/{slug}

Browser verification:
- Two-panel layout with Story (primary, 65%) and Chat (auxiliary, 35%)
- Top content block with "Demo Context" markdown content
- Story runtime available for start/auto-start
- Chat panel with participant mode

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
# PATH SETUP FOR AUTH HELPER
# =============================================================================
#
# The auth_helper module is in the same directory (test_scripts/).
# We add this directory to sys.path to enable imports regardless of
# where the script is executed from.
#
sys.path.insert(0, str(Path(__file__).parent))

from auth_helper import get_authenticated_session, AuthenticationError

# =============================================================================
# CONFIGURATION
# =============================================================================

# API Base URL - the backend must be running at this address
BASE_URL = "http://localhost:8000/api/v1"

# Default story ID for testing - can be overridden via --story-id flag
# This should be a valid Story UUID in your database
DEFAULT_STORY_ID = "172109da-8b5f-48f2-9e7a-4259657691dc"

# Slug prefix for auto-generated slugs
SLUG_PREFIX = "qa-baseline"

# Output file for test results
RESULTS_FILE = "test_results_qa_demo_baseline.json"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_slug(prefix: str = SLUG_PREFIX) -> str:
    """
    Generate a unique slug for a demo.

    Format: {prefix}-{timestamp}-{random}
    Example: qa-baseline-0221-1430-x7k2

    The timestamp provides rough ordering/identification,
    while the random suffix ensures uniqueness even for
    rapid successive runs.

    Args:
        prefix: Base prefix for the slug

    Returns:
        str: A unique, URL-safe slug
    """
    # Timestamp: MMDD-HHMM format (compact but identifiable)
    timestamp = datetime.now().strftime("%m%d-%H%M")

    # Random suffix: 4 lowercase alphanumeric characters
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

    return f"{prefix}-{timestamp}-{random_suffix}"


def generate_results_filename(slug: str) -> str:
    """
    Generate a results filename based on the demo slug.

    This ensures each run has its own results file, making it
    easier to track multiple test runs.

    Args:
        slug: The demo slug

    Returns:
        str: Filename for results JSON
    """
    return f"test_results_{slug.replace('-', '_')}.json"


# =============================================================================
# COMPOSITION PAYLOADS
# =============================================================================
#
# These payloads are extracted from qa-demo-composition-reference.md
# and structured for programmatic use. Each payload is documented with
# its purpose and the API behavior it triggers.
#

def get_baseline_composition(
    story_id: str | None = None,
    story_panel_size: int = 65,
    chat_panel_size: int = 35,
    with_participants: bool = False,
    participant_panel_size: int = 25,
    participant_options: dict | None = None
) -> dict[str, Any]:
    """
    Build the baseline template composition payload.

    This is the "Base Template (Full Replace)" from the reference document.
    It creates a two-panel layout with Story Runtime and Chat, plus a
    constant context block at the top.

    PANEL CONFIGURATION:
    ---------------------
    1. story-runtime-primary (kind: storyRuntime)
       - prominence: primary (main focus area)
       - default_size: 65 (occupies 65% of panel space)
       - options.send_runtime_events_to_chat: true
         → Story events (choices made, state changes) appear in chat
       - options.viewer_mode: false
         → Users can interact, not just observe

    2. chat-aux (kind: chat)
       - prominence: auxiliary (secondary area)
       - default_size: 35 (occupies 35% of panel space)
       - options.mode: participant
         → Users can send messages (vs observer = read-only)
       - options.include_internal_messages: false
         → System/agent internal messages are hidden

    BLOCK CONFIGURATION:
    --------------------
    1. context-top (type: context, region: top)
       - Constant content that persists during interaction
       - visibility: visible (not hidden by default)
       - content_json.format: markdown
         → Rendered as formatted text
       - content_json.metadata.variant: card
         → Styled with card appearance

    Args:
        story_id: Optional UUID string for the story to bind.
                  If provided, added to metadata_json.story_id.
                  If None, no story binding (demo room without story).
        story_panel_size: Default size for story panel (1-100, default 65)
        chat_panel_size: Default size for chat panel (1-100, default 35)
        with_participants: If True, add a participantPanel showing room users/agents
        participant_panel_size: Size for participant panel (1-100, default 25)
        participant_options: Optional dict of options for participantPanel:
            - showUsers: bool - Whether to show user section (default: true)
            - showAgents: bool - Whether to show agent section (default: true)
            - compact: bool - Use compact display mode (default: false)
            - allowQuickAdd: bool - Show quick-add agent button (default: true)

    Returns:
        dict: The composition payload ready for PUT request.

    API Behavior:
        When this composition is PUT to /demos/configs/{id}/composition:
        - Replaces any existing composition entirely
        - Validates all panel/block IDs are unique
        - Validates UUIDs for theme_id fields if present
        - If metadata_json.story_id is set, validates story exists
    """

    # -------------------------------------------------------------------------
    # BASE COMPOSITION STRUCTURE
    # -------------------------------------------------------------------------
    #
    # This follows the DemoPageComposition schema (schema_version: 1)
    #
    composition = {
        # Schema version - required for forward compatibility
        # Current version: 1
        "schema_version": 1,

        # Layout mode determines how panels are arranged
        # "panels": Split view with resizable panels
        # "tabs": Tabbed interface (one panel visible at a time)
        "layout_mode": "panels",

        # =====================================================================
        # RUNTIME POLICY
        # =====================================================================
        #
        # Controls how/when the story runtime starts:
        #
        # "auto":
        #   - Runtime starts automatically when session begins
        #   - Story advances to start node immediately
        #   - Good for demos where you want immediate engagement
        #
        # "manual":
        #   - Runtime requires explicit start action
        #   - User sees "Start" button before story begins
        #   - Good for tutorials or when setup is needed first
        #
        # "owner_only":
        #   - Only the demo owner can start the runtime
        #   - Viewers must wait for owner to initiate
        #   - Good for controlled presentations
        #
        "runtime_policy": "auto",

        # =====================================================================
        # PERSONA POLICY
        # =====================================================================
        #
        # Controls how the user's persona is assigned:
        #
        # "first_available":
        #   - System assigns the first available persona
        #   - Simplest option for most demos
        #
        # "fixed_user_persona":
        #   - Uses fixed_user_persona_id field
        #   - User always gets the specified persona
        #   - Requires: fixed_user_persona_id to be set
        #
        # "manual_prompt":
        #   - Prompts user to select their persona
        #   - Good for multi-character experiences
        #
        "persona_policy": "first_available",

        # =====================================================================
        # CHAT MODE
        # =====================================================================
        #
        # Default mode for chat panels:
        #
        # "participant":
        #   - User can send messages
        #   - Full chat interaction enabled
        #
        # "observer":
        #   - User can only read messages
        #   - Good for demo/presentation viewing
        #
        "chat_mode": "participant",

        # Optional theme bindings (null = use defaults)
        # These accept valid Theme UUIDs from your system
        "fixed_user_persona_id": None,  # Used with persona_policy: "fixed_user_persona"
        "page_theme_id": None,          # Page-level theme override
        "cards_theme_id": None,         # Cards/component theme override

        # Free-form presentation hints for the frontend
        # Not validated by backend, passed through to frontend
        "presentation_json": {},

        # =====================================================================
        # PANELS ARRAY
        # =====================================================================
        #
        # Each panel is a distinct interactive area.
        # Panels are rendered according to prominence and order.
        #
        "panels": [
            # -----------------------------------------------------------------
            # PANEL 1: Story Runtime (Primary)
            # -----------------------------------------------------------------
            #
            # This panel renders the interactive story experience.
            # As the "primary" panel, it gets visual emphasis.
            #
            {
                # Unique ID within this composition
                # Used for targeting in updates and frontend state
                "id": "story-runtime-primary",

                # Panel kind - determines the renderer
                # "storyRuntime" renders the story with choices
                "kind": "storyRuntime",

                # Prominence affects visual hierarchy
                # "primary" = main content area
                # "auxiliary" = supporting/sidebar content
                "prominence": "primary",

                # Order within same prominence level
                # Lower numbers appear first/leftmost
                "order": 1,

                # Display title for the panel
                "title": "Story",

                # Panel sizing (percentages)
                # default_size: Initial size when demo loads
                # min_size: Smallest allowed size
                # max_size: Largest allowed size
                "default_size": story_panel_size,
                "min_size": 30,
                "max_size": 85,

                # Viewport mode
                # "panel": Normal panel in split layout
                # "page": Full page takeover (only one per composition)
                "viewport_mode": "panel",

                # Kind-specific options for storyRuntime
                "options": {
                    # When true, story events are posted to the chat panel
                    # This creates a narrative log alongside the story
                    "send_runtime_events_to_chat": True,

                    # When true, user is in view-only mode
                    # When false, user can make choices
                    "viewer_mode": False
                }
            },

            # -----------------------------------------------------------------
            # PANEL 2: Chat (Auxiliary)
            # -----------------------------------------------------------------
            #
            # This panel renders the room chat.
            # As "auxiliary", it's visually secondary to the story panel.
            #
            {
                "id": "chat-aux",
                "kind": "chat",
                "prominence": "auxiliary",
                "order": 2,
                "title": "Chat",
                "default_size": chat_panel_size,
                "min_size": 20,
                "max_size": 50,
                "viewport_mode": "panel",

                # Kind-specific options for chat
                "options": {
                    # Chat mode at panel level
                    # Can override composition-level chat_mode
                    "mode": "participant",

                    # Whether to show internal/system messages
                    # false = cleaner user experience
                    # true = useful for debugging
                    "include_internal_messages": False
                }
            }
        ],

        # =====================================================================
        # BLOCKS ARRAY
        # =====================================================================
        #
        # Blocks are static/semi-static content regions.
        # They persist across panel interactions.
        # Good for instructions, context, status displays.
        #
        "blocks": [
            # -----------------------------------------------------------------
            # BLOCK 1: Context (Top Region)
            # -----------------------------------------------------------------
            #
            # This block appears at the top of the demo page.
            # It displays constant content that doesn't change during interaction.
            #
            {
                # Unique ID within this composition
                "id": "context-top",

                # Block type - determines rendering behavior
                # "context" = general informational content
                # "content" = raw content rendering
                # "story" = story-specific content
                # "agentRoster" = list of agents in room
                "type": "context",

                # Region determines placement
                # "top" = above panels
                # "primary" = within primary panel area
                # "auxiliary" = within auxiliary area
                # "footer" = below panels
                "region": "top",

                # Order within the region
                "order": 1,

                # Display title for the block
                "title": "Demo Context",

                # Visibility control
                # "visible" = shown by default
                # "hidden_unmounted" = not rendered
                # "hidden_mounted" = mounted but visually hidden
                "visibility": "visible",

                # Presentation hints for frontend
                "presentation_json": {},

                # Block configuration (type-specific)
                "config_json": {},

                # Content to display
                # This is what the user sees in the block
                "content_json": {
                    # Content format
                    # "markdown" = rendered as markdown
                    # "json" = rendered as formatted JSON
                    # "html" = rendered as HTML (sanitized)
                    # "code" = rendered as code block
                    "format": "markdown",

                    # The actual content
                    "value": "## Demo Context\nThis block stays constant while the user interacts with story and chat.",

                    # Content metadata
                    "metadata": {
                        # Visual variant
                        # "card" = card-style container
                        # Other values may be supported
                        "variant": "card",

                        # Optional label for the content
                        "label": "Overview"
                    }
                }
            }
        ],

        # =====================================================================
        # METADATA JSON
        # =====================================================================
        #
        # Free-form metadata for the composition.
        # Important: story_id goes here for story binding!
        #
        "metadata_json": {
            # Description of this composition
            "description": "QA baseline composition - created by test script",

            # Auto-respond setting for the room
            # When true, AI agents respond automatically
            "auto_respond": True
        }
    }

    # -------------------------------------------------------------------------
    # OPTIONAL: PARTICIPANT PANEL
    # -------------------------------------------------------------------------
    #
    # If with_participants is True, add a participantPanel to show who's in
    # the room. This panel displays:
    # - Human users with avatars and names
    # - AI agents with status, mode badges, and controls
    # - Quick-add functionality for adding agents
    #
    # The panel is added to the auxiliary area after chat.
    #
    if with_participants:
        # Build options dict, using defaults for any unspecified values
        panel_options = {
            # Whether to show the Users section
            "showUsers": True,
            # Whether to show the Agents section
            "showAgents": True,
            # Compact mode reduces visual density
            "compact": False,
            # Whether to show the quick-add agent button
            "allowQuickAdd": True,
        }
        # Merge in any user-provided options
        if participant_options:
            panel_options.update(participant_options)

        composition["panels"].append({
            "id": "participants",
            "kind": "participantPanel",
            "prominence": "auxiliary",
            "order": 3,  # After chat
            "title": "Participants",
            "default_size": participant_panel_size,
            "min_size": 15,
            "max_size": 40,
            "viewport_mode": "panel",
            "options": panel_options
        })

    # -------------------------------------------------------------------------
    # STORY BINDING
    # -------------------------------------------------------------------------
    #
    # If a story_id is provided, add it to metadata_json.
    # This tells the backend which story to use for the story runtime.
    #
    # Resolution order for story_id:
    # 1. composition.metadata_json.story_id (highest priority)
    # 2. demo_config.metadata_json.story_id
    # 3. null (no story)
    #
    if story_id:
        composition["metadata_json"]["story_id"] = story_id

    return composition


def get_demo_config_payload(slug: str, title: str | None = None) -> dict[str, Any]:
    """
    Build the DemoConfig creation payload.

    A DemoConfig represents a demo that can be accessed via its slug.
    It stores settings and references to compositions.

    Args:
        slug: URL-friendly identifier for the demo (e.g., "my-demo-name")
              Must be unique across all demos
        title: Human-readable title. Defaults to title-cased slug.

    Returns:
        dict: Payload for POST /api/v1/demos/

    DemoConfig fields:
    - slug: URL identifier (required, unique)
    - title: Display name
    - scope: "personal" | "public" | "team"
    - is_active: Whether the demo is accessible
    - default_auto_respond: Default auto-respond setting for sessions
    - metadata_json: Free-form configuration
    """

    # Generate title from slug if not provided
    if title is None:
        # Convert "qa-baseline-template" to "QA Baseline Template"
        title = slug.replace("-", " ").title()

    return {
        # URL-friendly slug - used in /demo/{slug} routes
        "slug": slug,

        # Display title
        "title": title,

        # Scope determines visibility
        # "personal" = only owner can access
        # "public" = anyone can access
        # "team" = team members can access
        "scope": "personal",

        # Whether the demo is active and accessible
        "is_active": True,

        # Default auto-respond for new sessions
        # Can be overridden per-session
        "default_auto_respond": True,

        # Free-form metadata
        "metadata_json": {
            "created_by": "test_qa_demo_baseline.py",
            "created_at": datetime.now().isoformat(),
            "purpose": "QA testing of demo composition system"
        }
    }


# =============================================================================
# DEMO COMPOSITION BUILDER CLASS
# =============================================================================

class DemoCompositionBuilder:
    """
    Orchestrates the demo composition test workflow.

    This class encapsulates all API interactions needed to:
    1. Create a DemoConfig
    2. Attach a composition
    3. Create a session
    4. Validate the results

    It maintains state for tracking created resources and supports
    cleanup operations.
    """

    def __init__(
        self,
        session: requests.Session,
        story_id: str | None = None,
        demo_slug: str | None = None,
        verbose: bool = False,
        story_panel_size: int = 65,
        chat_panel_size: int = 35,
        with_participants: bool = False,
        participant_panel_size: int = 25,
        participant_options: dict | None = None
    ):
        """
        Initialize the builder.

        Args:
            session: Authenticated requests.Session from auth_helper
            story_id: Story UUID to bind to the demo (optional)
            demo_slug: Slug for the demo (used in URLs). Auto-generated if None.
            verbose: If True, print detailed debug output
            story_panel_size: Default size for story panel (1-100)
            chat_panel_size: Default size for chat panel (1-100)
            with_participants: If True, add a participantPanel
            participant_panel_size: Size for participant panel (1-100)
            participant_options: Optional dict of options for participantPanel
        """
        self.session = session
        self.story_id = story_id
        self.demo_slug = demo_slug or generate_slug()
        self.verbose = verbose
        self.story_panel_size = story_panel_size
        self.chat_panel_size = chat_panel_size
        self.with_participants = with_participants
        self.participant_panel_size = participant_panel_size
        self.participant_options = participant_options

        # Track created resources for cleanup
        self.demo_config_id: str | None = None
        self.demo_config: dict | None = None
        self.composition_response: dict | None = None
        self.session_response: dict | None = None

        # Track test results
        self.results = {
            "test_name": "QA Demo Baseline Template",
            "start_time": datetime.now().isoformat(),
            "story_id": story_id,
            "demo_slug": demo_slug,
            "steps": [],
            "success": False,
            "errors": []
        }

    # =========================================================================
    # LOGGING HELPERS
    # =========================================================================

    def log(self, message: str):
        """Print a log message."""
        print(f"  {message}")

    def debug(self, message: str):
        """Print a debug message if verbose mode is enabled."""
        if self.verbose:
            print(f"  [DEBUG] {message}")

    def log_step(self, step_name: str, success: bool, details: str = ""):
        """Record a test step result."""
        self.results["steps"].append({
            "step": step_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        status = "✓" if success else "✗"
        self.log(f"{status} {step_name}" + (f" - {details}" if details else ""))

    # =========================================================================
    # API INTERACTION METHODS
    # =========================================================================

    def create_demo_config(self) -> dict:
        """
        Create a new DemoConfig via POST /api/v1/demos/.

        API Details:
        - Method: POST
        - Endpoint: /api/v1/demos/
        - Request Body: DemoConfigCreate schema
        - Response: DemoConfig with id, owner_id, created_at, etc.

        The slug must be unique. If a demo with this slug already exists,
        the API will return a 400 error.

        Returns:
            dict: The created DemoConfig object

        Raises:
            Exception: If API call fails or slug already exists
        """
        self.log("\n📦 Creating DemoConfig...")

        payload = get_demo_config_payload(self.demo_slug)

        self.debug(f"POST {BASE_URL}/demos/")
        self.debug(f"Payload: {json.dumps(payload, indent=2)}")

        response = self.session.post(
            f"{BASE_URL}/demos/",
            json=payload
        )

        # API returns 201 Created for successful POST (resource creation)
        if response.status_code in (200, 201):
            self.demo_config = response.json()
            self.demo_config_id = self.demo_config["id"]

            self.log_step(
                "Create DemoConfig",
                True,
                f"id={self.demo_config_id}, slug={self.demo_slug}"
            )

            self.debug(f"Response: {json.dumps(self.demo_config, indent=2)}")

            return self.demo_config

        elif response.status_code == 400:
            # Likely a duplicate slug
            error_detail = response.json().get("detail", response.text)
            self.log_step("Create DemoConfig", False, f"400: {error_detail}")
            raise Exception(f"Failed to create DemoConfig: {error_detail}")

        else:
            self.log_step(
                "Create DemoConfig",
                False,
                f"HTTP {response.status_code}"
            )
            raise Exception(
                f"Failed to create DemoConfig: {response.status_code} - {response.text}"
            )

    def set_composition(self) -> dict:
        """
        Set the composition via PUT /api/v1/demos/configs/{id}/composition.

        API Details:
        - Method: PUT (full replace)
        - Endpoint: /api/v1/demos/configs/{demo_config_id}/composition
        - Request Body: DemoPageComposition schema
        - Response: Updated DemoConfig with composition attached

        PUT replaces the entire composition. Use PATCH for partial updates.

        The composition is validated:
        - Panel/block IDs must be unique
        - Theme UUIDs must reference existing themes (if provided)
        - Story UUID must reference existing story (if provided)

        Returns:
            dict: The updated DemoConfig with composition

        Raises:
            Exception: If API call fails or validation fails
        """
        if not self.demo_config_id:
            raise Exception("No DemoConfig created. Call create_demo_config() first.")

        self.log("\n🎨 Setting composition...")

        composition = get_baseline_composition(
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

        # PUT typically returns 200, but accept 201 for consistency
        if response.status_code in (200, 201):
            self.composition_response = response.json()

            # Extract key info for logging
            panels_count = len(composition.get("panels", []))
            blocks_count = len(composition.get("blocks", []))
            has_story = "story_id" in composition.get("metadata_json", {})

            self.log_step(
                "Set Composition",
                True,
                f"{panels_count} panels, {blocks_count} blocks, story={has_story}"
            )

            self.debug(f"Response: {json.dumps(self.composition_response, indent=2)}")

            return self.composition_response

        elif response.status_code == 400:
            error_detail = response.json().get("detail", response.text)
            self.log_step("Set Composition", False, f"400: {error_detail}")
            raise Exception(f"Failed to set composition: {error_detail}")

        elif response.status_code == 404:
            self.log_step("Set Composition", False, "DemoConfig not found")
            raise Exception(f"DemoConfig {self.demo_config_id} not found")

        else:
            self.log_step("Set Composition", False, f"HTTP {response.status_code}")
            raise Exception(
                f"Failed to set composition: {response.status_code} - {response.text}"
            )

    def create_session(self) -> dict:
        """
        Create/retrieve a demo session via POST /api/v1/demos/{slug}/session.

        API Details:
        - Method: POST
        - Endpoint: /api/v1/demos/{slug}/session
        - Request Body: Empty or optional session config
        - Response: DemoSessionResolved with composition, room, runtime

        This endpoint:
        1. Finds or creates a DemoSession for the current user
        2. Resolves the composition (inheritance, defaults)
        3. Creates or retrieves the Room for the session
        4. Initializes the StoryRuntime if story_id is bound
        5. Returns all resolved contexts

        Key response fields:
        - session_id: UUID of the demo session
        - composition: The resolved composition
        - composition_source: Where composition came from
        - room: The chat room context
        - runtime: The story runtime context (if story bound)

        Returns:
            dict: The DemoSessionResolved object

        Raises:
            Exception: If API call fails or demo not found
        """
        self.log("\n🚀 Creating demo session...")

        self.debug(f"POST {BASE_URL}/demos/{self.demo_slug}/session")

        response = self.session.post(
            f"{BASE_URL}/demos/{self.demo_slug}/session"
        )

        # API may return 200 (existing session) or 201 (new session created)
        if response.status_code in (200, 201):
            self.session_response = response.json()

            # Extract key info for logging
            session_id = self.session_response.get("session_id", "N/A")
            has_room = "room" in self.session_response
            has_runtime = "runtime" in self.session_response
            composition_source = self.session_response.get("composition_source", "N/A")

            self.log_step(
                "Create Session",
                True,
                f"session={session_id[:8]}..., room={has_room}, runtime={has_runtime}"
            )

            self.debug(f"Response: {json.dumps(self.session_response, indent=2)}")

            return self.session_response

        elif response.status_code == 404:
            self.log_step("Create Session", False, f"Demo '{self.demo_slug}' not found")
            raise Exception(f"Demo '{self.demo_slug}' not found")

        elif response.status_code == 400:
            error_detail = response.json().get("detail", response.text)
            self.log_step("Create Session", False, f"400: {error_detail}")
            raise Exception(f"Failed to create session: {error_detail}")

        else:
            self.log_step("Create Session", False, f"HTTP {response.status_code}")
            raise Exception(
                f"Failed to create session: {response.status_code} - {response.text}"
            )

    def delete_demo(self, demo_config_id: str | None = None) -> bool:
        """
        Delete a DemoConfig and its associated resources.

        API Details:
        - Method: DELETE
        - Endpoint: /api/v1/demos/configs/{demo_config_id}
        - Response: 200 OK on success

        This cascades to delete:
        - All sessions for this demo
        - The composition
        - Associated room/runtime references (but not the rooms themselves)

        Args:
            demo_config_id: UUID of demo to delete. Uses self.demo_config_id if not provided.

        Returns:
            bool: True if deletion successful
        """
        target_id = demo_config_id or self.demo_config_id

        if not target_id:
            self.log("⚠️ No demo_config_id provided for deletion")
            return False

        self.log(f"\n🗑️ Deleting DemoConfig {target_id}...")

        response = self.session.delete(
            f"{BASE_URL}/demos/configs/{target_id}"
        )

        # DELETE may return 200 (with body) or 204 (no content)
        if response.status_code in (200, 204):
            self.log_step("Delete DemoConfig", True, f"id={target_id}")
            return True
        elif response.status_code == 404:
            self.log_step("Delete DemoConfig", False, "Not found")
            return False
        else:
            self.log_step("Delete DemoConfig", False, f"HTTP {response.status_code}")
            return False

    def list_demos(self, limit: int = 20) -> list[dict]:
        """
        List existing demo configs.

        API Details:
        - Method: GET
        - Endpoint: /api/v1/demos/
        - Query params: skip, limit
        - Response: { data: [...], count: N }

        Returns:
            list: Array of DemoConfig objects
        """
        self.log("\n📋 Listing demo configs...")

        response = self.session.get(
            f"{BASE_URL}/demos/",
            params={"limit": limit}
        )

        if response.status_code == 200:
            data = response.json()
            demos = data.get("data", [])
            count = data.get("count", len(demos))
            self.log(f"  Found {count} demo(s)")
            return demos
        else:
            self.log(f"  ❌ Failed to list demos: {response.status_code}")
            return []

    def get_demo_by_slug(self, slug: str) -> dict | None:
        """
        Get a demo config by its slug.

        API Details:
        - Method: GET
        - Endpoint: /api/v1/demos/{slug}
        - Response: DemoConfig with composition

        Args:
            slug: The demo's URL slug

        Returns:
            dict: DemoConfig object or None if not found
        """
        self.log(f"\n🔍 Getting demo: {slug}")

        response = self.session.get(f"{BASE_URL}/demos/{slug}")

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            self.log(f"  ⚠️ Demo '{slug}' not found")
            return None
        else:
            self.log(f"  ❌ Failed: {response.status_code}")
            return None

    def get_composition(self, demo_config_id: str) -> dict | None:
        """
        Get the composition for a demo config.

        API Details:
        - Method: GET
        - Endpoint: /api/v1/demos/configs/{id}/composition
        - Response: DemoPageComposition

        Args:
            demo_config_id: UUID of the demo config

        Returns:
            dict: Composition object or None if not found
        """
        response = self.session.get(
            f"{BASE_URL}/demos/configs/{demo_config_id}/composition"
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None

    # =========================================================================
    # MAIN WORKFLOW
    # =========================================================================

    def run_full_workflow(self, skip_session: bool = False) -> bool:
        """
        Execute the complete demo creation workflow.

        Steps:
        1. Create DemoConfig with slug and settings
        2. Attach composition with panels and blocks
        3. Create session to verify everything works (unless skip_session=True)

        Args:
            skip_session: If True, skip the session creation step.
                          Useful for testing composition without full session.

        Returns:
            bool: True if all steps completed successfully
        """
        try:
            # Step 1: Create the DemoConfig
            self.create_demo_config()

            # Step 2: Set the composition
            self.set_composition()

            # Step 3: Create session (optional)
            if not skip_session:
                self.create_session()
            else:
                self.log("\n⏭️ Skipping session creation (--no-session)")

            self.results["success"] = True
            return True

        except Exception as e:
            self.results["errors"].append(str(e))
            self.results["success"] = False
            raise


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main() -> int:
    """
    Main entry point for the test script.

    Parses command line arguments and executes the appropriate workflow.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """

    # =========================================================================
    # ARGUMENT PARSING
    # =========================================================================

    parser = argparse.ArgumentParser(
        description="Test QA Demo Composition - Baseline Template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Auto-generate slug, use default story
  %(prog)s --story-id abc123...               # Use specific story
  %(prog)s --slug my-test-demo                # Use explicit slug (no auto-generate)
  %(prog)s --verbose                          # Show debug output
  %(prog)s --no-session                       # Skip session creation
  %(prog)s --no-story                         # Create demo without story binding
  %(prog)s --dry-run                          # Show what would be created
  %(prog)s --list                             # List existing demos
  %(prog)s --get SLUG                         # Get composition for existing demo
  %(prog)s --cleanup --demo-config-id xyz...  # Delete a demo

Panel size customization:
  %(prog)s --story-size 70 --chat-size 30     # Custom panel sizes
        """
    )

    # =========================================================================
    # STORY BINDING OPTIONS
    # =========================================================================

    story_group = parser.add_mutually_exclusive_group()

    story_group.add_argument(
        "--story-id",
        type=str,
        default=DEFAULT_STORY_ID,
        help=f"Story UUID to bind to the demo (default: {DEFAULT_STORY_ID})"
    )

    story_group.add_argument(
        "--no-story",
        action="store_true",
        help="Create demo without story binding (chat-only or manual setup)"
    )

    # =========================================================================
    # DEMO IDENTIFICATION
    # =========================================================================

    parser.add_argument(
        "--slug",
        type=str,
        default=None,  # None = auto-generate
        help="Explicit slug for the demo URL (default: auto-generated)"
    )

    # =========================================================================
    # PANEL CUSTOMIZATION
    # =========================================================================

    parser.add_argument(
        "--story-size",
        type=int,
        default=65,
        metavar="PCT",
        help="Default size for story panel, 1-100 (default: 65)"
    )

    parser.add_argument(
        "--chat-size",
        type=int,
        default=35,
        metavar="PCT",
        help="Default size for chat panel, 1-100 (default: 35)"
    )

    parser.add_argument(
        "--with-participants",
        action="store_true",
        help="Add a participant panel showing room users and agents"
    )

    parser.add_argument(
        "--participant-size",
        type=int,
        default=25,
        metavar="PCT",
        help="Size for participant panel when enabled (default: 25)"
    )

    parser.add_argument(
        "--participant-options",
        type=str,
        default=None,
        metavar="JSON",
        help='JSON options for participantPanel, e.g. \'{"showAgents": true}\''
    )

    # =========================================================================
    # WORKFLOW CONTROL
    # =========================================================================

    parser.add_argument(
        "--no-session",
        action="store_true",
        help="Skip session creation (test composition only)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making API calls"
    )

    # =========================================================================
    # INSPECTION MODES
    # =========================================================================

    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing demo configs and exit"
    )

    parser.add_argument(
        "--get",
        type=str,
        metavar="SLUG",
        help="Get and display composition for an existing demo"
    )

    # =========================================================================
    # OUTPUT CONTROL
    # =========================================================================

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug output"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for scripting)"
    )

    # =========================================================================
    # CLEANUP MODE
    # =========================================================================

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the demo instead of creating it"
    )

    parser.add_argument(
        "--demo-config-id",
        type=str,
        help="DemoConfig UUID to delete (required with --cleanup)"
    )

    args = parser.parse_args()

    # =========================================================================
    # DETERMINE STORY ID
    # =========================================================================
    #
    # Priority:
    # 1. --no-story flag → None (no story binding)
    # 2. --story-id value → Use that UUID
    # 3. Default → DEFAULT_STORY_ID
    #
    story_id = None if args.no_story else args.story_id

    # =========================================================================
    # DETERMINE SLUG
    # =========================================================================
    #
    # If --slug is provided, use it exactly.
    # Otherwise, auto-generate a unique slug.
    #
    demo_slug = args.slug  # Will be None if not provided, triggering auto-gen

    # =========================================================================
    # DRY RUN MODE
    # =========================================================================

    # Parse participant_options JSON if provided
    participant_options = None
    if args.participant_options:
        try:
            participant_options = json.loads(args.participant_options)
        except json.JSONDecodeError as e:
            print(f"\n❌ Invalid JSON for --participant-options: {e}")
            return 1

    if args.dry_run:
        generated_slug = demo_slug or generate_slug()
        composition = get_baseline_composition(
            story_id=story_id,
            story_panel_size=args.story_size,
            chat_panel_size=args.chat_size,
            with_participants=args.with_participants,
            participant_panel_size=args.participant_size,
            participant_options=participant_options
        )

        print("\n" + "=" * 70)
        print("  DRY RUN - No API calls will be made")
        print("=" * 70)
        print(f"\n  Would create demo with slug: {generated_slug}")
        print(f"  Story ID: {story_id or 'None (no story)'}")
        print(f"  Panel sizes: Story={args.story_size}%, Chat={args.chat_size}%")
        if args.with_participants:
            print(f"  Participant panel: {args.participant_size}%")
        print("\n  Composition payload:")
        print(json.dumps(composition, indent=2))
        print("\n" + "=" * 70 + "\n")
        return 0

    # =========================================================================
    # SCRIPT EXECUTION
    # =========================================================================

    print("\n" + "=" * 70)
    print("  QA DEMO COMPOSITION TEST - BASELINE TEMPLATE")
    print("  Testing demo composition system with panels and blocks")
    print("=" * 70)

    try:
        # Authenticate
        print("\n🔐 Authenticating...")
        session = get_authenticated_session()
        print("  ✓ Authentication successful")

        # Create builder
        builder = DemoCompositionBuilder(
            session=session,
            story_id=story_id,
            demo_slug=demo_slug,  # None triggers auto-generation
            verbose=args.verbose,
            story_panel_size=args.story_size,
            chat_panel_size=args.chat_size,
            with_participants=args.with_participants,
            participant_panel_size=args.participant_size,
            participant_options=participant_options
        )

        # =====================================================================
        # LIST MODE
        # =====================================================================

        if args.list:
            demos = builder.list_demos()
            if demos:
                print("\n  Existing demos:")
                print("  " + "-" * 66)
                print(f"  {'SLUG':<30} {'ID':<36} {'ACTIVE'}")
                print("  " + "-" * 66)
                for demo in demos:
                    slug = demo.get("slug", "N/A")[:30]
                    demo_id = demo.get("id", "N/A")
                    is_active = "✓" if demo.get("is_active") else "✗"
                    print(f"  {slug:<30} {demo_id:<36} {is_active}")
                print("  " + "-" * 66)
            else:
                print("\n  No demos found.")
            return 0

        # =====================================================================
        # GET MODE
        # =====================================================================

        if args.get:
            demo = builder.get_demo_by_slug(args.get)
            if demo:
                demo_id = demo.get("id")
                composition = builder.get_composition(demo_id) if demo_id else None

                if args.json:
                    # JSON output for scripting
                    output = {"demo": demo, "composition": composition}
                    print(json.dumps(output, indent=2))
                else:
                    print(f"\n  Demo: {args.get}")
                    print(f"  ID: {demo_id}")
                    print(f"  Title: {demo.get('title', 'N/A')}")
                    print(f"  Active: {demo.get('is_active', False)}")
                    print(f"  Owner: {demo.get('owner_id', 'N/A')}")

                    if composition:
                        panels = composition.get("panels", [])
                        blocks = composition.get("blocks", [])
                        print(f"\n  Composition:")
                        print(f"    Layout: {composition.get('layout_mode', 'N/A')}")
                        print(f"    Runtime Policy: {composition.get('runtime_policy', 'N/A')}")
                        print(f"    Panels: {len(panels)}")
                        for p in panels:
                            print(f"      - {p.get('id')}: {p.get('kind')} ({p.get('prominence')}, {p.get('default_size', '?')}%)")
                        print(f"    Blocks: {len(blocks)}")
                        for b in blocks:
                            print(f"      - {b.get('id')}: {b.get('type')} ({b.get('region')})")

                        # Show story_id if present
                        meta = composition.get("metadata_json", {})
                        if "story_id" in meta:
                            print(f"\n    Story ID: {meta['story_id']}")
                    else:
                        print("\n  ⚠️ No composition attached")
                return 0
            else:
                return 1

        # =====================================================================
        # CLEANUP MODE
        # =====================================================================

        if args.cleanup:
            if not args.demo_config_id:
                print("\n❌ --cleanup requires --demo-config-id")
                return 1

            success = builder.delete_demo(args.demo_config_id)
            return 0 if success else 1

        # =====================================================================
        # CREATE MODE (Default)
        # =====================================================================

        # Run the full workflow
        builder.run_full_workflow(skip_session=args.no_session)

        # =====================================================================
        # SUCCESS SUMMARY
        # =====================================================================

        print("\n" + "=" * 70)
        print("  TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print(f"\n  Demo Config ID: {builder.demo_config_id}")
        print(f"  Demo Slug: {builder.demo_slug}")
        print(f"  Story ID: {story_id or 'None (no story bound)'}")
        print(f"  Panel Sizes: Story={args.story_size}%, Chat={args.chat_size}%")

        print("\n  Composition Structure:")
        print("  ┌─────────────────────────────────────────────────────┐")
        print("  │  [context-top] Demo Context (markdown, card)       │")
        print("  ├───────────────────────────┬─────────────────────────┤")
        print(f"  │  story-runtime-primary    │  chat-aux               │")
        print(f"  │  (storyRuntime)           │  (chat)                 │")
        print(f"  │  primary, {args.story_size}%{' ' * (13 - len(str(args.story_size)))}│  auxiliary, {args.chat_size}%{' ' * (10 - len(str(args.chat_size)))}│")
        print("  │  auto-start               │  participant mode       │")
        print("  └───────────────────────────┴─────────────────────────┘")

        print(f"\n  🌐 Access the demo at:")
        print(f"     http://localhost:5173/demo/{builder.demo_slug}")

        if builder.session_response:
            session_id = builder.session_response.get("session_id", "N/A")
            print(f"\n  📍 Session ID: {session_id}")

        # Save results with dynamic filename
        results_file = generate_results_filename(builder.demo_slug)
        builder.results["end_time"] = datetime.now().isoformat()
        builder.results["demo_slug"] = builder.demo_slug  # Update with actual slug used
        with open(results_file, "w") as f:
            json.dump(builder.results, f, indent=2)
        print(f"\n  📄 Results saved to: {results_file}")

        print("\n  🧹 To clean up, run:")
        print(f"     python {Path(__file__).name} --cleanup --demo-config-id {builder.demo_config_id}")

        # If JSON output requested, also print machine-readable summary
        if args.json:
            print("\n  JSON Summary:")
            summary = {
                "demo_config_id": builder.demo_config_id,
                "slug": builder.demo_slug,
                "story_id": story_id,
                "url": f"http://localhost:5173/demo/{builder.demo_slug}",
                "success": True
            }
            print(json.dumps(summary, indent=2))

        print("\n" + "=" * 70 + "\n")

        return 0

    except AuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure test.env exists with TEST_USER_EMAIL and TEST_USER_PASSWORD")
        print("   2. Verify backend is running at localhost:8000")
        print("   3. Confirm test user credentials are correct")
        return 1

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
