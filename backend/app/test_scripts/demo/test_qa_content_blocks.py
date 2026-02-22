#!/usr/bin/env python3
"""
QA Content Block Browser Validation Test Script

This script tests the content rendering system across different formats:
- Markdown (headings, lists, inline code)
- Code (Shiki syntax highlighting, line numbers, copy button)
- JSON (tree view, interactive mode)
- HTML (sanitization, safe rendering)
- Region ordering and visibility

=============================================================================
PURPOSE
=============================================================================

This validates that content blocks render correctly in the browser using
the ContentRenderer system. It tests:

1. **Markdown format** - Headings, lists, inline code, links
2. **Code format** - Syntax highlighting, line numbers, highlighted lines
3. **JSON format** - Tree view, interactive mode
4. **HTML format** - Safe rendering with script sanitization
5. **Region ordering** - Blocks appear in correct order
6. **Visibility** - Hidden blocks don't render

=============================================================================
CONTENT FORMATS
=============================================================================

Each format has specific options in content_json.metadata.options:

MARKDOWN:
  - No special options needed, just format: "markdown"

CODE:
  - language: "python" | "javascript" | "typescript" | etc.
  - lineNumbers: true | false
  - highlightLines: [1, 2, 3]  (1-indexed)
  - copyable: true | false

JSON:
  - viewMode: "tree" | "raw"
  - interactive: true | false

HTML:
  - sanitize: true | false (should always be true for safety)

=============================================================================
USAGE
=============================================================================

Run specific content format test:
    python test_qa_content_blocks.py --format markdown
    python test_qa_content_blocks.py --format code
    python test_qa_content_blocks.py --format json
    python test_qa_content_blocks.py --format html
    python test_qa_content_blocks.py --format regions

Run all formats (creates multiple demos):
    python test_qa_content_blocks.py --all

Dry run to see payloads:
    python test_qa_content_blocks.py --format code --dry-run

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
SLUG_PREFIX = "qa-content"


def generate_slug(format_name: str) -> str:
    timestamp = datetime.now().strftime("%m%d-%H%M")
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{SLUG_PREFIX}-{format_name}-{timestamp}-{suffix}"


def generate_results_filename(slug: str) -> str:
    return f"test_results_{slug.replace('-', '_')}.json"


# =============================================================================
# COMPOSITION PAYLOADS FOR EACH FORMAT
# =============================================================================

def get_markdown_composition() -> dict[str, Any]:
    """
    Markdown content block in top region.

    Tests:
    - Heading rendering (##)
    - List rendering (- bullets)
    - Inline code (`backticks`)
    - Card variant styling
    """
    return {
        "schema_version": 1,
        "layout_mode": "panels",
        "runtime_policy": "manual",
        "persona_policy": "first_available",
        "chat_mode": "participant",
        "panels": [
            {
                "id": "chat",
                "kind": "chat",
                "prominence": "primary",
                "order": 1,
                "title": "Chat"
            }
        ],
        "blocks": [
            {
                "id": "md-top",
                "type": "context",
                "region": "top",
                "order": 1,
                "title": "Overview",
                "visibility": "visible",
                "content_json": {
                    "format": "markdown",
                    "value": """## Markdown Block Test

This tests markdown rendering:

- **Bold text** and *italic text*
- Bullet point A
- Bullet point B
- `inline code` rendering

### Code example
```python
def hello():
    print("world")
```

> Blockquote text

[Link text](https://example.com)""",
                    "metadata": {
                        "variant": "card"
                    }
                }
            }
        ],
        "metadata_json": {
            "description": "QA Markdown content block test",
            "test_type": "content_markdown"
        }
    }


def get_code_composition() -> dict[str, Any]:
    """
    Code content block with Shiki highlighting.

    Tests:
    - Syntax highlighting (Python)
    - Line numbers display
    - Highlighted lines
    - Copy button on hover
    """
    return {
        "schema_version": 1,
        "layout_mode": "panels",
        "runtime_policy": "manual",
        "persona_policy": "first_available",
        "chat_mode": "participant",
        "panels": [
            {
                "id": "chat",
                "kind": "chat",
                "prominence": "auxiliary",
                "order": 2,
                "title": "Chat"
            }
        ],
        "blocks": [
            {
                "id": "code-top",
                "type": "content",
                "region": "top",
                "order": 1,
                "title": "Code Snippet",
                "visibility": "visible",
                "content_json": {
                    "format": "code",
                    "value": """def greet(name: str) -> str:
    \"\"\"Generate a greeting message.\"\"\"
    return f"Hello, {name}!"

def main():
    message = greet("World")
    print(message)

if __name__ == "__main__":
    main()""",
                    "metadata": {
                        "variant": "card",
                        "options": {
                            # Language for syntax highlighting
                            "language": "python",
                            # Show line numbers
                            "lineNumbers": True,
                            # Highlight specific lines (1-indexed)
                            "highlightLines": [2, 3],
                            # Show copy button
                            "copyable": True
                        }
                    }
                }
            }
        ],
        "metadata_json": {
            "description": "QA Code content block with Shiki highlighting",
            "test_type": "content_code"
        }
    }


def get_json_composition() -> dict[str, Any]:
    """
    JSON content in a panel (not block).

    Tests:
    - JSON tree view mode
    - Interactive expand/collapse
    - Nested object rendering
    - Array rendering
    """
    return {
        "schema_version": 1,
        "layout_mode": "panels",
        "runtime_policy": "manual",
        "persona_policy": "first_available",
        "chat_mode": "participant",
        "panels": [
            {
                "id": "json-content",
                "kind": "content",
                "prominence": "primary",
                "order": 1,
                "title": "JSON Content",
                "default_size": 60,
                "options": {
                    # Content panel uses options.content_json
                    "content_json": {
                        "format": "json",
                        "value": {
                            "testCase": "content-panel-json",
                            "user": {
                                "name": "Test User",
                                "email": "test@example.com",
                                "roles": ["admin", "editor"]
                            },
                            "settings": {
                                "theme": "dark",
                                "notifications": True,
                                "language": "en"
                            },
                            "items": [
                                {"id": 1, "name": "Item A"},
                                {"id": 2, "name": "Item B"},
                                {"id": 3, "name": "Item C"}
                            ],
                            "flags": {
                                "featureA": True,
                                "featureB": False,
                                "featureC": None
                            }
                        },
                        "metadata": {
                            "variant": "card",
                            "options": {
                                # Tree view with expand/collapse
                                "viewMode": "tree",
                                # Allow interactive expansion
                                "interactive": True
                            }
                        }
                    }
                }
            },
            {
                "id": "chat",
                "kind": "chat",
                "prominence": "auxiliary",
                "order": 2,
                "title": "Chat",
                "default_size": 40
            }
        ],
        "blocks": [],
        "metadata_json": {
            "description": "QA JSON content panel test",
            "test_type": "content_json"
        }
    }


def get_html_composition() -> dict[str, Any]:
    """
    HTML content block with sanitization.

    Tests:
    - HTML structure rendering
    - Script tag sanitization (should NOT execute)
    - Safe HTML elements (div, p, h3, strong)
    - Sanitize option honored
    """
    return {
        "schema_version": 1,
        "layout_mode": "panels",
        "runtime_policy": "manual",
        "persona_policy": "first_available",
        "chat_mode": "participant",
        "panels": [
            {
                "id": "chat",
                "kind": "chat",
                "prominence": "primary",
                "order": 1,
                "title": "Chat"
            }
        ],
        "blocks": [
            {
                "id": "html-top",
                "type": "content",
                "region": "top",
                "order": 1,
                "title": "HTML Content",
                "visibility": "visible",
                "content_json": {
                    "format": "html",
                    # Intentionally includes script tag to test sanitization
                    "value": """<div class="test-container">
  <h3>Safe HTML Rendering Test</h3>
  <p>This paragraph has <strong>bold</strong> and <em>italic</em> text.</p>
  <ul>
    <li>List item 1</li>
    <li>List item 2</li>
  </ul>
  <p style="color: blue;">Styled text (may be stripped)</p>
  <script>alert('XSS Test - This should NOT execute!')</script>
  <img src="x" onerror="alert('XSS via img')">
</div>""",
                    "metadata": {
                        "variant": "card",
                        "options": {
                            # CRITICAL: Always sanitize HTML
                            "sanitize": True
                        }
                    }
                }
            }
        ],
        "metadata_json": {
            "description": "QA HTML content with sanitization test",
            "test_type": "content_html_safety"
        }
    }


def get_regions_composition(story_id: str | None = None) -> dict[str, Any]:
    """
    Multiple blocks testing region ordering and visibility.

    Tests:
    - Top region with multiple blocks in order
    - Auxiliary region block
    - Hidden block (should not render)
    - Footer region
    - Story integration (optional)
    """
    composition = {
        "schema_version": 1,
        "layout_mode": "panels",
        "runtime_policy": "auto" if story_id else "manual",
        "persona_policy": "first_available",
        "chat_mode": "participant",
        "panels": [
            {
                "id": "story",
                "kind": "storyRuntime",
                "prominence": "primary",
                "order": 1,
                "title": "Story",
                "default_size": 60
            },
            {
                "id": "chat",
                "kind": "chat",
                "prominence": "auxiliary",
                "order": 2,
                "title": "Chat",
                "default_size": 40
            }
        ],
        "blocks": [
            # Top region - order 2 (should appear SECOND)
            {
                "id": "top-2",
                "type": "content",
                "region": "top",
                "order": 2,
                "title": "Top Block (Order 2)",
                "visibility": "visible",
                "content_json": {
                    "format": "markdown",
                    "value": "**Top block order 2** - Should appear SECOND in top region",
                    "metadata": {"variant": "card"}
                }
            },
            # Top region - order 1 (should appear FIRST)
            {
                "id": "top-1",
                "type": "content",
                "region": "top",
                "order": 1,
                "title": "Top Block (Order 1)",
                "visibility": "visible",
                "content_json": {
                    "format": "markdown",
                    "value": "**Top block order 1** - Should appear FIRST in top region",
                    "metadata": {"variant": "card"}
                }
            },
            # Auxiliary region
            {
                "id": "aux-note",
                "type": "content",
                "region": "auxiliary",
                "order": 1,
                "title": "Auxiliary Block",
                "visibility": "visible",
                "content_json": {
                    "format": "markdown",
                    "value": "**Auxiliary region** - Should appear near auxiliary panel",
                    "metadata": {"variant": "card"}
                }
            },
            # Hidden block - should NOT render
            {
                "id": "hidden-one",
                "type": "content",
                "region": "footer",
                "order": 1,
                "title": "Hidden Block",
                "visibility": "hidden_unmounted",
                "content_json": {
                    "format": "markdown",
                    "value": "**THIS SHOULD NOT BE VISIBLE** - Hidden block test",
                    "metadata": {"variant": "card"}
                }
            },
            # Footer region (visible)
            {
                "id": "footer-visible",
                "type": "content",
                "region": "footer",
                "order": 2,
                "title": "Footer Block",
                "visibility": "visible",
                "content_json": {
                    "format": "markdown",
                    "value": "**Footer region** - Should appear at bottom",
                    "metadata": {"variant": "card"}
                }
            }
        ],
        "metadata_json": {
            "description": "QA Region ordering and visibility test",
            "test_type": "content_regions"
        }
    }

    if story_id:
        composition["metadata_json"]["story_id"] = story_id

    return composition


# =============================================================================
# FORMAT REGISTRY
# =============================================================================

FORMATS = {
    "markdown": {
        "name": "Markdown",
        "composition_fn": get_markdown_composition,
        "description": "Markdown rendering (headings, lists, code)",
        "needs_story": False
    },
    "code": {
        "name": "Code (Shiki)",
        "composition_fn": get_code_composition,
        "description": "Code with syntax highlighting, line numbers",
        "needs_story": False
    },
    "json": {
        "name": "JSON Panel",
        "composition_fn": get_json_composition,
        "description": "JSON tree view in content panel",
        "needs_story": False
    },
    "html": {
        "name": "HTML Safety",
        "composition_fn": get_html_composition,
        "description": "HTML rendering with XSS sanitization",
        "needs_story": False
    },
    "regions": {
        "name": "Regions & Visibility",
        "composition_fn": get_regions_composition,
        "description": "Region ordering, hidden blocks, story integration",
        "needs_story": True
    }
}


def get_demo_config_payload(slug: str, format_name: str) -> dict[str, Any]:
    format_info = FORMATS.get(format_name, {})
    return {
        "slug": slug,
        "title": f"QA Content: {format_info.get('name', format_name)}",
        "scope": "personal",
        "is_active": True,
        "default_auto_respond": True,
        "metadata_json": {
            "created_by": "test_qa_content_blocks.py",
            "created_at": datetime.now().isoformat(),
            "test_scenario": f"content_{format_name}",
            "format": format_name
        }
    }


# =============================================================================
# DEMO BUILDER CLASS
# =============================================================================

class ContentBlockBuilder:
    """Orchestrates content block test workflow."""

    def __init__(
        self,
        session: requests.Session,
        format_name: str,
        story_id: str | None = None,
        demo_slug: str | None = None,
        verbose: bool = False,
        with_participants: bool = False,
        participant_panel_size: int = 20,
        participant_options: dict | None = None
    ):
        self.session = session
        self.format_name = format_name
        self.story_id = story_id
        self.demo_slug = demo_slug or generate_slug(format_name)
        self.verbose = verbose
        self.with_participants = with_participants
        self.participant_panel_size = participant_panel_size
        self.participant_options = participant_options

        self.demo_config_id: str | None = None
        self.demo_config: dict | None = None
        self.composition_response: dict | None = None
        self.session_response: dict | None = None

        self.results = {
            "test_name": f"QA Content Block - {format_name}",
            "start_time": datetime.now().isoformat(),
            "format": format_name,
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
        payload = get_demo_config_payload(self.demo_slug, self.format_name)
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

        format_info = FORMATS[self.format_name]
        if format_info.get("needs_story"):
            composition = format_info["composition_fn"](self.story_id)
        else:
            composition = format_info["composition_fn"]()

        # Add participant panel if requested
        if self.with_participants:
            panel_opts = {
                "showUsers": True,
                "showAgents": True,
                "compact": False,
                "allowQuickAdd": True
            }
            if self.participant_options:
                panel_opts.update(self.participant_options)

            # Find the max order in existing panels
            max_order = max((p.get("order", 0) for p in composition.get("panels", [])), default=0)

            composition["panels"].append({
                "id": "participants",
                "kind": "participantPanel",
                "prominence": "auxiliary",
                "order": max_order + 1,
                "title": "Participants",
                "default_size": self.participant_panel_size,
                "min_size": 15,
                "max_size": 35,
                "viewport_mode": "panel",
                "options": panel_opts
            })
            composition["metadata_json"]["with_participants"] = True

        self.debug(f"Composition: {json.dumps(composition, indent=2)}")

        response = self.session.put(
            f"{BASE_URL}/demos/configs/{self.demo_config_id}/composition",
            json=composition
        )
        if response.status_code in (200, 201):
            self.composition_response = response.json()
            self.log_step("Set Composition", True, f"format={self.format_name}")
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
        description="Test QA Content Blocks - Various Format Rendering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available formats:
{chr(10).join(f'  {k:12} - {v["description"]}' for k, v in FORMATS.items())}
        """
    )

    parser.add_argument("--format", "-f", type=str, choices=list(FORMATS.keys()),
        help="Content format to test")
    parser.add_argument("--all", action="store_true",
        help="Run all format tests (creates multiple demos)")

    parser.add_argument("--story-id", type=str, default=DEFAULT_STORY_ID,
        help="Story UUID for region test")
    parser.add_argument("--slug", type=str, default=None,
        help="Custom slug (only for single format)")

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
    parser.add_argument("--list-formats", action="store_true",
        help="List available formats and exit")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--demo-config-id", type=str)

    args = parser.parse_args()

    if args.list_formats:
        print("\nAvailable content formats:")
        print("-" * 60)
        for key, info in FORMATS.items():
            story_note = " (requires story)" if info.get("needs_story") else ""
            print(f"  {key:12} - {info['description']}{story_note}")
        print("-" * 60)
        return 0

    if not args.format and not args.all and not args.list and not args.cleanup:
        parser.print_help()
        print("\n❌ Specify --format FORMAT or --all")
        return 1

    # Parse participant options if provided
    participant_options = None
    if args.participant_options:
        try:
            participant_options = json.loads(args.participant_options)
        except json.JSONDecodeError as e:
            print(f"\n❌ Invalid JSON for --participant-options: {e}")
            return 1

    print("\n" + "=" * 70)
    print("  QA CONTENT BLOCK TESTS")
    print("=" * 70)

    try:
        print("\n🔐 Authenticating...")
        session = get_authenticated_session()
        print("  ✓ Authentication successful")

        # List mode
        if args.list:
            builder = ContentBlockBuilder(session, "markdown")
            demos = builder.list_demos()
            print("\n  Existing demos:")
            for d in demos:
                print(f"    {d.get('slug', 'N/A'):<40} {d.get('id', 'N/A')}")
            return 0

        # Cleanup mode
        if args.cleanup:
            if not args.demo_config_id:
                print("\n❌ --cleanup requires --demo-config-id")
                return 1
            builder = ContentBlockBuilder(session, "markdown")
            return 0 if builder.delete_demo(args.demo_config_id) else 1

        # Determine which formats to run
        formats_to_run = list(FORMATS.keys()) if args.all else [args.format]

        created_demos = []

        for format_name in formats_to_run:
            format_info = FORMATS[format_name]
            print(f"\n{'='*70}")
            print(f"  Testing format: {format_info['name']}")
            print(f"  {format_info['description']}")
            print("=" * 70)

            if args.dry_run:
                slug = args.slug or generate_slug(format_name)
                if format_info.get("needs_story"):
                    comp = format_info["composition_fn"](args.story_id)
                else:
                    comp = format_info["composition_fn"]()

                # Add participant panel for dry run if requested
                if args.with_participants:
                    panel_opts = {"showUsers": True, "showAgents": True, "compact": False, "allowQuickAdd": True}
                    if participant_options:
                        panel_opts.update(participant_options)
                    max_order = max((p.get("order", 0) for p in comp.get("panels", [])), default=0)
                    comp["panels"].append({
                        "id": "participants", "kind": "participantPanel", "prominence": "auxiliary",
                        "order": max_order + 1, "title": "Participants",
                        "default_size": args.participant_size, "min_size": 15, "max_size": 35,
                        "viewport_mode": "panel", "options": panel_opts
                    })

                print(f"\n  Slug: {slug}")
                if args.with_participants:
                    print(f"  Participant Panel: size={args.participant_size}%")
                print("\n  Composition:")
                print(json.dumps(comp, indent=2))
                continue

            builder = ContentBlockBuilder(
                session=session,
                format_name=format_name,
                story_id=args.story_id if format_info.get("needs_story") else None,
                demo_slug=args.slug if len(formats_to_run) == 1 else None,
                verbose=args.verbose,
                with_participants=args.with_participants,
                participant_panel_size=args.participant_size,
                participant_options=participant_options
            )

            builder.run_full_workflow(skip_session=args.no_session)

            created_demos.append({
                "format": format_name,
                "slug": builder.demo_slug,
                "id": builder.demo_config_id,
                "url": f"http://localhost:5173/demo/{builder.demo_slug}"
            })

            print(f"\n  ✓ {format_info['name']}: http://localhost:5173/demo/{builder.demo_slug}")

            # Save individual results
            results_file = generate_results_filename(builder.demo_slug)
            builder.results["end_time"] = datetime.now().isoformat()
            with open(results_file, "w") as f:
                json.dump(builder.results, f, indent=2)

        if not args.dry_run:
            print("\n" + "=" * 70)
            print("  ALL TESTS COMPLETED")
            print("=" * 70)

            print("\n  Created demos:")
            for demo in created_demos:
                print(f"    {demo['format']:12} → {demo['url']}")

            print("\n  Expected behaviors to verify:")
            print("    markdown  - Headings, lists, code blocks render correctly")
            print("    code      - Syntax highlighting, line numbers, copy button")
            print("    json      - Tree view, expand/collapse, interactive mode")
            print("    html      - Safe elements render, scripts are sanitized")
            print("    regions   - Blocks ordered correctly, hidden block invisible")

            print("\n  Cleanup commands:")
            for demo in created_demos:
                print(f"    python {Path(__file__).name} --cleanup --demo-config-id {demo['id']}")

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
