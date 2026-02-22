#!/usr/bin/env python3
"""
Seed Script: The Antiquarian's Journal Demo

Creates the Antiquarian story via the existing builder and wires it into the
new DemoConfig/DemoSession flow so it can be opened at /demo/{slug}.

What this script creates:
- Story + nodes + choices + state schema (via AntiquarianJournalBuilder)
- DemoConfig (slug-based)
- DemoSession (for current user) + session room
- Persona + UserPersona for runtime initialization
- Room runtime initialization for the demo session room

Usage:
    python seed_antiquarian_journal_demo.py
    python seed_antiquarian_journal_demo.py --verbose
    python seed_antiquarian_journal_demo.py --json
    python seed_antiquarian_journal_demo.py --slug antiquarian-journal
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Local helpers / builders
sys.path.append(str(Path(__file__).parent))
from auth_helper import AuthenticationError, get_authenticated_session
from test_antiquarian_journal_story import AntiquarianJournalBuilder

BASE_URL = "http://localhost:8000/api/v1"


def log(message: str, verbose: bool = True) -> None:
    if verbose:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")


def _attach_story_to_room(room_id: str, story_id: str, verbose: bool = True) -> None:
    """
    Patch room.story_id directly in DB.

    Current Rooms PATCH API only exposes title updates, so story_id association
    for demo-created session rooms is applied here.
    """
    try:
        from sqlmodel import Session
        from app.core.db import engine
        from app.models import Room
    except Exception as exc:
        raise RuntimeError(
            "Unable to import DB models. Run from backend project root so 'app' is importable."
        ) from exc

    room_uuid = uuid.UUID(room_id)
    story_uuid = uuid.UUID(story_id)

    with Session(engine) as db:
        room = db.get(Room, room_uuid)
        if room is None:
            raise RuntimeError(f"Room not found in DB: {room_id}")
        room.story_id = story_uuid
        db.add(room)
        db.commit()
        log(f"  ✅ Room {room_id[:8]}... linked to story {story_id[:8]}...", verbose)


def _ensure_demo_config(
    session: requests.Session,
    *,
    slug: str,
    story_id: str,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Get or create a DemoConfig by slug.
    """
    # Check existing configs visible to current user.
    resp = session.get(f"{BASE_URL}/demos", params={"limit": 200, "include_inactive": True})
    resp.raise_for_status()
    configs = resp.json().get("data", [])
    existing = next((c for c in configs if c.get("slug") == slug), None)

    default_panels = [
        {
            "id": "story",
            "kind": "story",
            "title": "Story",
            "prominence": "primary",
            "default_size": 65,
            "min_size": 30,
            "viewport_mode": "panel",
        },
        {
            "id": "chat",
            "kind": "chat",
            "title": "Chat",
            "prominence": "auxiliary",
            "default_size": 35,
            "min_size": 20,
            "viewport_mode": "panel",
        },
    ]
    default_layout = [
        {"id": "story", "order": 1, "default_size": 65, "min_size": 30},
        {"id": "chat", "order": 2, "default_size": 35, "min_size": 20},
    ]
    metadata = {"seed_story_id": story_id, "seed_kind": "antiquarian_journal"}

    if existing:
        log(f"  ℹ️  Demo config already exists for slug '{slug}', reusing", verbose)
        return existing

    payload = {
        "slug": slug,
        "title": "The Antiquarian's Journal",
        "description": "Markdown-rich narrative demo with branching story runtime.",
        "scope": "personal",
        "is_active": True,
        "default_auto_respond": True,
        "default_panels_json": default_panels,
        "default_layout_json": default_layout,
        "metadata_json": metadata,
    }
    resp = session.post(f"{BASE_URL}/demos", json=payload)
    resp.raise_for_status()
    created = resp.json()
    log(f"  ✅ Demo config created: {created['id'][:8]}... slug={slug}", verbose)
    return created


def seed_antiquarian_journal_demo(
    session: requests.Session,
    *,
    slug: str = "antiquarian-journal",
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Execute full demo seed flow.
    """
    results: dict[str, Any] = {}

    # 1) Build story content using existing builder
    log("Creating Antiquarian story...", verbose)
    builder = AntiquarianJournalBuilder(session, verbose=verbose)
    is_valid = builder.build_story()
    if not is_valid:
        raise RuntimeError("Antiquarian story schema validation failed.")
    story_id = builder.story_id
    if not story_id:
        raise RuntimeError("Builder did not return a story ID.")
    results["story_id"] = story_id
    results["story_nodes_count"] = len(builder.nodes)
    results["story_choices_count"] = len(builder.choices)

    # 2) Publish story for runtime usage
    log("Publishing story...", verbose)
    resp = session.put(f"{BASE_URL}/stories/{story_id}/publish")
    resp.raise_for_status()
    published = resp.json()
    story_version = published.get("published_version") or 1
    results["published_version"] = story_version
    log(f"  ✅ Story published: v{story_version}", verbose)

    # 3) Create or fetch demo config
    log("Ensuring demo config...", verbose)
    demo_config = _ensure_demo_config(session, slug=slug, story_id=story_id, verbose=verbose)
    results["demo_config_id"] = demo_config["id"]
    results["demo_slug"] = demo_config["slug"]

    # 4) Resolve session (creates room for current user if missing)
    log("Resolving demo session...", verbose)
    resp = session.post(f"{BASE_URL}/demos/{slug}/session")
    resp.raise_for_status()
    resolved = resp.json()
    demo_session = resolved["demo_session"]
    room_id = demo_session["room_id"]
    results["demo_session_id"] = demo_session["id"]
    results["room_id"] = room_id
    results["session_created"] = resolved.get("created", False)
    log(
        f"  ✅ Demo session {'created' if resolved.get('created') else 'reused'}: "
        f"{demo_session['id'][:8]}... room={room_id[:8]}...",
        verbose,
    )

    # 5) Attach story to session room (DB patch) + init runtime
    log("Linking session room to story...", verbose)
    _attach_story_to_room(room_id=room_id, story_id=story_id, verbose=verbose)

    # 6) Create persona + user-persona for runtime init
    log("Creating runtime persona...", verbose)
    resp = session.post(
        f"{BASE_URL}/personas",
        json={
            "name": "Antiquarian Reader",
            "description": "A careful reader tracing uncertain truths.",
        },
    )
    resp.raise_for_status()
    persona = resp.json()
    results["persona_id"] = persona["id"]

    resp = session.post(f"{BASE_URL}/user-personas", json={"persona_id": persona["id"]})
    resp.raise_for_status()
    user_persona = resp.json()
    results["user_persona_id"] = user_persona["id"]
    log(f"  ✅ UserPersona created: {user_persona['id'][:8]}...", verbose)

    # 7) Initialize runtime
    log("Initializing room runtime...", verbose)
    resp = session.put(
        f"{BASE_URL}/rooms/{room_id}/runtime",
        json={
            "user_persona_id": user_persona["id"],
            "story_version": story_version,
        },
    )
    resp.raise_for_status()
    runtime = resp.json()
    results["room_runtime"] = {
        "active_progress_id": runtime.get("active_progress_id"),
        "revision": runtime.get("revision"),
        "current_node_id": runtime.get("current_node_id"),
    }
    log("  ✅ Runtime initialized", verbose)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Antiquarian Journal demo")
    parser.add_argument("--slug", default="antiquarian-journal", help="Demo slug")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output only JSON")
    args = parser.parse_args()

    verbose = not args.json
    if args.verbose:
        verbose = True

    try:
        session = get_authenticated_session()
        if verbose:
            print("=" * 68)
            print("  SEED: THE ANTIQUARIAN'S JOURNAL DEMO")
            print("=" * 68)

        results = seed_antiquarian_journal_demo(
            session,
            slug=args.slug,
            verbose=verbose,
        )

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print()
            print("=" * 68)
            print("  SEED COMPLETE")
            print("=" * 68)
            print(json.dumps(results, indent=2))
            print()
            print(f"Demo URL: http://localhost:5173/demo/{results['demo_slug']}")
            print(f"Story URL: http://localhost:5173/stories/{results['story_id']}/play")

    except AuthenticationError as exc:
        print(f"❌ Authentication failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        body = exc.response.text if exc.response is not None else str(exc)
        print(f"❌ API error: {status} - {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"❌ Unexpected error: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
