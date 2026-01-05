#!/usr/bin/env python3
"""
Debug script for validate-state endpoint failure
Tests the /validate-state endpoint with the latest test run data
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session

BASE_URL = "http://localhost:8000/api/v1"

def main():
    s = get_authenticated_session()

    # Load latest test results
    results_file = Path(__file__).parent / "test_results_story_system.json"
    if not results_file.exists():
        print("❌ No test results file found. Run test_story_system.py first.")
        return

    with open(results_file) as f:
        results = json.load(f)

    persona_id = results['test_entities']['persona_id']
    story_id = results['test_entities']['story_id']

    print("=" * 70)
    print("  VALIDATE-STATE ENDPOINT DEBUG")
    print("=" * 70)
    print(f"\nPersona ID: {persona_id}")
    print(f"Story ID: {story_id}")

    # Get current progress state
    print("\n" + "-" * 70)
    print("  Step 1: Get Current Progress")
    print("-" * 70)

    prog_resp = s.get(f"{BASE_URL}/user-personas/{persona_id}/stories/{story_id}")
    if prog_resp.status_code != 200:
        print(f"❌ Failed to get progress: {prog_resp.status_code}")
        print(f"   {prog_resp.text}")
        return

    prog = prog_resp.json()
    print(f"✅ Progress retrieved:")
    print(f"   head_choice_id: {prog.get('head_choice_id') or 'None (at start)'}")
    print(f"   head_version: {prog.get('head_version')}")
    print(f"   current_node_id: {prog.get('current_node_id')}")
    print(f"   story_state: {prog.get('story_state')}")
    print(f"   is_completed: {prog.get('is_completed')}")

    # Try to get head choice details if not None
    if prog.get('head_choice_id'):
        print("\n" + "-" * 70)
        print("  Step 2: Examine Head Choice")
        print("-" * 70)

        # Try to get the choice via timeline
        timeline_resp = s.get(f"{BASE_URL}/user-personas/{persona_id}/stories/{story_id}/timeline")
        if timeline_resp.status_code == 200:
            timeline = timeline_resp.json()
            print(f"✅ Timeline retrieved:")
            print(f"   Total events: {len(timeline.get('events', []))}")
            print(f"   Head version: {timeline.get('head_version')}")
            print(f"\n   Events:")
            for i, event in enumerate(timeline.get('events', []), 1):
                is_current = "← CURRENT" if event.get('is_current') else ""
                print(f"     {i}. {event.get('choice_text')} → {event.get('node_title')} {is_current}")

    # Call validate-state endpoint
    print("\n" + "-" * 70)
    print("  Step 3: Call validate-state Endpoint")
    print("-" * 70)

    val_resp = s.get(f"{BASE_URL}/user-personas/{persona_id}/stories/{story_id}/validate-state")
    print(f"Status: {val_resp.status_code}")

    if val_resp.status_code != 200:
        print(f"❌ FAILED")
        print(f"\nResponse:")
        print(val_resp.text[:1000])
    else:
        print(f"✅ SUCCESS")
        result = val_resp.json()
        print(f"\nValidation Result:")
        print(f"   Match: {result.get('match')}")
        print(f"   Stored state: {result.get('stored_state')}")
        print(f"   Replayed state: {result.get('replayed_state')}")
        if result.get('differences'):
            print(f"   Differences: {result.get('differences')}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
