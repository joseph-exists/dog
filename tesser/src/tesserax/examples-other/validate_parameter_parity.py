#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tesserax.parity import load_parity_manifest, validate_parity_manifest


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fail-fast parameter parity gate for migrated examples."
    )
    p.add_argument(
        "--manifest",
        type=str,
        default="examples-other/parameter_parity_manifest.json",
        help="Path to parity manifest JSON.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    payload = load_parity_manifest(manifest_path)
    issues = validate_parity_manifest(payload)
    if issues:
        print("PARITY_GATE: FAIL")
        print(f"manifest={manifest_path}")
        print(f"issue_count={len(issues)}")
        for reason in issues:
            print(f"reason={reason}")
        raise SystemExit(2)

    examples = payload.get("examples", [])
    print("PARITY_GATE: PASS")
    print(f"manifest={manifest_path}")
    print(f"examples={len(examples)}")


if __name__ == "__main__":
    main()
