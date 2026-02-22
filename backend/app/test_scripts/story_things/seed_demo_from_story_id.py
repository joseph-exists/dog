#!/usr/bin/env python3
"""
Slim Seed Script: Create Demo from Existing Story ID

This script wires an existing story into the DemoConfig/DemoSession flow.
It does NOT create story nodes/choices; it only creates demo runtime scaffolding.

Creates:
- DemoConfig (or reuses existing slug)
- DemoSession for current user (via /demos/{slug}/session)
- Links session room -> provided story_id (DB patch)
- Persona + UserPersona
- Room runtime initialization

Usage:
    python seed_demo_from_story_id.py --story-id <uuid>
    python seed_demo_from_story_id.py --story-id <uuid> --slug antiquarian-journal
    python seed_demo_from_story_id.py --story-id <uuid> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

sys.path.append(str(Path(__file__).parent))
from auth_helper import AuthenticationError, get_authenticated_session

BASE_URL = "http://localhost:8000/api/v1"


def log(message: str, verbose: bool = True) -> None:
    if verbose:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {message}")


def slugify(value: str) -> str:
    s = value.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s[:60] or "story-demo"


def _attach_story_to_room(room_id: str, story_id: str, verbose: bool = True) -> None:
    """
    Patch room.story_id directly in DB.
    Rooms PATCH currently only supports title updates.
    """
    try:
        from sqlmodel import Session
        from app.core.db import engine
        from app.models import Room
    except Exception as exc:
        raise RuntimeError(
            "DB imports failed. Run this from backend root so 'app' is importable."
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
        log(f"  ✅ Linked room {room_id[:8]}... -> story {story_id[:8]}...", verbose)


def _get_story(session: requests.Session, story_id: str) -> dict[str, Any]:
    resp = session.get(f"{BASE_URL}/stories/{story_id}")
    resp.raise_for_status()
    return resp.json()


def _ensure_story_published(session: requests.Session, story_id: str, verbose: bool = True) -> int:
    story = _get_story(session, story_id)
    published_version = story.get("published_version")
    if published_version:
        log(f"  ℹ️  Story already published (v{published_version})", verbose)
        return int(published_version)

    log("Publishing story...", verbose)
    resp = session.put(f"{BASE_URL}/stories/{story_id}/publish")
    resp.raise_for_status()
    payload = resp.json()
    version = int(payload.get("published_version") or story.get("current_version") or 1)
    log(f"  ✅ Story published (v{version})", verbose)
    return version


def _ensure_demo_config(
    session: requests.Session,
    *,
    slug: str,
    title: str,
    story_id: str,
    verbose: bool = True,
) -> dict[str, Any]:
    # Check existing visible configs first.
    resp = session.get(f"{BASE_URL}/demos", params={"limit": 200, "include_inactive": True})
    resp.raise_for_status()
    configs = resp.json().get("data", [])
    existing = next((c for c in configs if c.get("slug") == slug), None)
    if existing:
        log(f"  ℹ️  Reusing existing DemoConfig slug='{slug}'", verbose)
        return existing

    payload = {
        "slug": slug,
        "title": title,
        "description": f"Demo runtime for story {story_id}",
        "scope": "personal",
        "is_active": True,
        "default_auto_respond": True,
        "default_panels_json": [
            {
                "id": "story",
                "kind": "story",
                "title": "Story",
                "prominence": "primary",
                "default_size": 65,
                "min_size": 30,
            },
            {
                "id": "chat",
                "kind": "chat",
                "title": "Chat",
                "prominence": "auxiliary",
                "default_size": 35,
                "min_size": 20,
            },
        ],
        "default_layout_json": [
            {"id": "story", "order": 1, "default_size": 65, "min_size": 30},
            {"id": "chat", "order": 2, "default_size": 35, "min_size": 20},
        ],
        "metadata_json": {"seed_story_id": story_id, "seed_kind": "story_id_slim"},
    }
    resp = session.post(f"{BASE_URL}/demos", json=payload)
    resp.raise_for_status()
    created = resp.json()
    log(f"  ✅ DemoConfig created: {created['id'][:8]}... slug='{slug}'", verbose)
    return created


def seed_demo_from_story_id(
    session: requests.Session,
    *,
    story_id: str,
    slug: str | None,
    verbose: bool = True,
) -> dict[str, Any]:
    results: dict[str, Any] = {"story_id": story_id}

    # Validate UUID upfront.
    uuid.UUID(story_id)

    story = _get_story(session, story_id)
    title = story.get("title") or "Story Demo"
    demo_slug = slug or slugify(title)

    version = _ensure_story_published(session, story_id, verbose=verbose)
    results["published_version"] = version

    log("Ensuring DemoConfig...", verbose)
    config = _ensure_demo_config(
        session,
        slug=demo_slug,
        title=title,
        story_id=story_id,
        verbose=verbose,
    )
    results["demo_config_id"] = config["id"]
    results["demo_slug"] = config["slug"]

    log("Resolving DemoSession...", verbose)
    resp = session.post(f"{BASE_URL}/demos/{demo_slug}/session")
    resp.raise_for_status()
    resolved = resp.json()
    demo_session = resolved["demo_session"]
    room_id = demo_session["room_id"]
    results["demo_session_id"] = demo_session["id"]
    results["room_id"] = room_id
    results["session_created"] = bool(resolved.get("created"))
    log(
        f"  ✅ DemoSession {'created' if resolved.get('created') else 'reused'}: "
        f"{demo_session['id'][:8]}... room={room_id[:8]}...",
        verbose,
    )

    log("Linking room to story...", verbose)
    _attach_story_to_room(room_id=room_id, story_id=story_id, verbose=verbose)

    log("Creating Persona/UserPersona...", verbose)
    resp = session.post(
        f"{BASE_URL}/personas",
        json={
            "name": f"{title[:40]} Reader",
            "description": "Runtime persona for story demo session",
        },
    )
    resp.raise_for_status()
    persona = resp.json()
    results["persona_id"] = persona["id"]

    resp = session.post(f"{BASE_URL}/user-personas", json={"persona_id": persona["id"]})
    resp.raise_for_status()
    user_persona = resp.json()
    results["user_persona_id"] = user_persona["id"]

    log("Initializing room runtime...", verbose)
    resp = session.put(
        f"{BASE_URL}/rooms/{room_id}/runtime",
        json={
            "user_persona_id": user_persona["id"],
            "story_version": version,
        },
    )
    resp.raise_for_status()
    runtime = resp.json()
    results["room_runtime"] = {
        "active_progress_id": runtime.get("active_progress_id"),
        "revision": runtime.get("revision"),
        "current_node_id": runtime.get("current_node_id"),
    }

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Create demo runtime from existing story ID")
    parser.add_argument("--story-id", required=True, help="Existing story UUID")
    parser.add_argument("--slug", default=None, help="Demo slug (optional)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    verbose = not args.json
    if args.verbose:
        verbose = True

    try:
        session = get_authenticated_session()
        if verbose:
            print("=" * 64)
            print("  SLIM SEED: DEMO FROM STORY ID")
            print("=" * 64)

        results = seed_demo_from_story_id(
            session,
            story_id=args.story_id,
            slug=args.slug,
            verbose=verbose,
        )

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print()
            print("=" * 64)
            print("  DONE")
            print("=" * 64)
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
