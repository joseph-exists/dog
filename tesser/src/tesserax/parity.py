from __future__ import annotations

import json
from pathlib import Path
from typing import Any


VALID_STATUSES = {"preserved", "aliased", "deprecated"}


def load_parity_manifest(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return payload


def validate_parity_manifest(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    examples = payload.get("examples")
    if not isinstance(examples, list) or not examples:
        return ["[E000] parity manifest must contain a non-empty 'examples' list."]

    for idx, example in enumerate(examples):
        prefix = f"examples[{idx}]"
        if not isinstance(example, dict):
            issues.append(f"[E001] {prefix} must be an object.")
            continue
        name = str(example.get("example", "")).strip()
        if not name:
            issues.append(f"[E002] {prefix}.example is required.")
            name = prefix

        rows = example.get("rows")
        if not isinstance(rows, list) or not rows:
            issues.append(f"[E003] {name}: rows must be a non-empty list.")
            continue

        required = example.get("required_high_impact", [])
        if not isinstance(required, list):
            issues.append(f"[E004] {name}: required_high_impact must be a list.")
            required = []
        required_set = {str(x) for x in required}

        by_legacy: dict[str, dict[str, Any]] = {}
        for ridx, row in enumerate(rows):
            rprefix = f"{name}.rows[{ridx}]"
            if not isinstance(row, dict):
                issues.append(f"[E005] {rprefix} must be an object.")
                continue
            legacy = str(row.get("legacy_param", "")).strip()
            mapping = str(row.get("new_api", "")).strip()
            status = str(row.get("status", "")).strip()
            if not legacy:
                issues.append(f"[E006] {rprefix} missing legacy_param.")
                continue
            if legacy in by_legacy:
                issues.append(f"[E007] {name}: duplicate legacy_param '{legacy}'.")
                continue
            by_legacy[legacy] = row
            if not mapping:
                issues.append(f"[E008] {name}: '{legacy}' has empty new_api mapping.")
            if status not in VALID_STATUSES:
                allowed = ", ".join(sorted(VALID_STATUSES))
                issues.append(
                    f"[E009] {name}: '{legacy}' has invalid status '{status}'. Allowed: {allowed}."
                )

        for required_legacy in sorted(required_set):
            if required_legacy not in by_legacy:
                issues.append(
                    f"[E010] {name}: required high-impact parameter '{required_legacy}' is missing."
                )
                continue
            row = by_legacy[required_legacy]
            status = str(row.get("status", "")).strip()
            if status == "deprecated":
                issues.append(
                    f"[E011] {name}: required high-impact parameter '{required_legacy}' cannot be deprecated."
                )

    return issues
