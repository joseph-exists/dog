#!/usr/bin/env python3
"""
Debug script for [ENDPOINT/FEATURE]

Quick investigation script for testing specific endpoints or debugging issues.
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session

BASE_URL = "http://localhost:8000/api/v1"


def main():
    s = get_authenticated_session()

    print("=" * 70)
    print("  [FEATURE] DEBUG")
    print("=" * 70)

    # ----------------------------------------------------------------
    # Step 1: Get initial state
    # ----------------------------------------------------------------
    print("\n" + "-" * 70)
    print("  Step 1: [Description]")
    print("-" * 70)

    response = s.get(f"{BASE_URL}/endpoint")

    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        print(f"   {response.text}")
        return

    data = response.json()
    print(f"✅ Success:")
    print(f"   Field 1: {data.get('field1')}")
    print(f"   Field 2: {data.get('field2')}")

    # ----------------------------------------------------------------
    # Step 2: Perform action
    # ----------------------------------------------------------------
    print("\n" + "-" * 70)
    print("  Step 2: [Description]")
    print("-" * 70)

    payload = {"key": "value"}
    response = s.post(f"{BASE_URL}/endpoint", json=payload)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ SUCCESS")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ FAILED")
        print(response.text[:500])

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
