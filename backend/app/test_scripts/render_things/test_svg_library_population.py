#!/usr/bin/env python3
"""
SVG Library Population Smoke Test

Validates that combinatoric planning + rendering produce API-safe SVG payloads and,
optionally, performs a live API smoke test against `/api/v1/svgs`.

Usage:
  python app/test_scripts/render_things/test_svg_library_population.py
  python app/test_scripts/render_things/test_svg_library_population.py --count 32 --seed 20260315
  python app/test_scripts/render_things/test_svg_library_population.py --post --create-count 5 --cleanup
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from svg_library_tools import build_asset_metadata, build_generation_plan, render_svg, validate_svg


def test_render_svg_imported_from_tesser():
    """render_svg and validate_svg should come from tesserax svg_compose after refactor."""
    from svg_library_tools import render_svg, validate_svg, build_generation_plan
    plan = build_generation_plan(total_count=4, seed=42)
    for row in plan["rows"]:
        svg = render_svg(row)
        assert validate_svg(svg) == [], f"Row {row.get('scenario_id')} produced invalid SVG"

BASE_URL = "http://localhost:8000/api/v1"


def _import_auth_helper():
    typer_dir = Path(__file__).resolve().parents[1] / "typer"
    if str(typer_dir) not in sys.path:
        sys.path.append(str(typer_dir))
    from auth_helper import get_authenticated_session  # type: ignore

    return get_authenticated_session


def run_local_validation(count: int, seed: int) -> dict[str, Any]:
    plan = build_generation_plan(total_count=count, seed=seed)
    failures: list[dict[str, Any]] = []
    for row in plan["rows"]:
        svg = render_svg(row)
        errors = validate_svg(svg)
        if errors:
            failures.append({"scenario_id": row["scenario_id"], "errors": errors})
            continue
        _ = build_asset_metadata(row, svg)
    return {
        "count": count,
        "seed": seed,
        "pairwise_coverage_pct": plan["meta"]["pairwise_coverage_pct"],
        "failures": failures,
        "failure_count": len(failures),
    }


def run_api_smoke(count: int, seed: int, create_count: int, cleanup: bool) -> dict[str, Any]:
    get_authenticated_session = _import_auth_helper()
    session = get_authenticated_session()
    plan = build_generation_plan(total_count=count, seed=seed)
    rows = plan["rows"][:create_count]

    created_private: list[str] = []
    created_public: list[str] = []
    failures: list[dict[str, Any]] = []

    for row in rows:
        svg_markup = render_svg(row)
        payload = {
            "visibility": "private",
            "name": f"smoke-{row['scenario_id']}",
            "description": "smoke test private asset",
            "svg_markup": svg_markup,
            "metadata_json": build_asset_metadata(row, svg_markup),
        }
        resp = session.post(f"{BASE_URL}/svgs", json=payload)
        if resp.status_code not in (200, 201):
            failures.append(
                {
                    "stage": "create-private",
                    "scenario_id": row["scenario_id"],
                    "status": resp.status_code,
                    "body": resp.text[:400],
                }
            )
            continue
        created_private.append(str(resp.json()["id"]))

    if created_private:
        first_id = created_private[0]
        patch_resp = session.patch(
            f"{BASE_URL}/svgs/{first_id}",
            json={"description": "smoke test patched description"},
        )
        if patch_resp.status_code != 200:
            failures.append(
                {
                    "stage": "patch",
                    "asset_id": first_id,
                    "status": patch_resp.status_code,
                    "body": patch_resp.text[:400],
                }
            )

        public_resp = session.post(
            f"{BASE_URL}/svgs",
            json={
                "visibility": "public",
                "source_private_id": first_id,
                "name": f"smoke-public-{first_id[:8]}",
                "description": "smoke test public copy",
            },
        )
        if public_resp.status_code in (200, 201):
            created_public.append(str(public_resp.json()["id"]))
        else:
            failures.append(
                {
                    "stage": "create-public",
                    "source_private_id": first_id,
                    "status": public_resp.status_code,
                    "body": public_resp.text[:400],
                }
            )

    list_resp = session.get(f"{BASE_URL}/svgs", params={"limit": 20, "skip": 0})
    if list_resp.status_code != 200:
        failures.append(
            {
                "stage": "list",
                "status": list_resp.status_code,
                "body": list_resp.text[:400],
            }
        )

    if cleanup:
        for asset_id in created_public + created_private:
            session.delete(f"{BASE_URL}/svgs/{asset_id}")

    return {
        "attempted_private": len(rows),
        "created_private": created_private,
        "created_public": created_public,
        "failure_count": len(failures),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SVG library generation + API smoke tester")
    parser.add_argument("--count", type=int, default=24, help="Number of planned scenarios")
    parser.add_argument("--seed", type=int, default=20260315, help="Deterministic generation seed")
    parser.add_argument("--post", action="store_true", help="Execute live API smoke test")
    parser.add_argument("--create-count", type=int, default=4, help="How many assets to POST in smoke mode")
    parser.add_argument("--cleanup", action="store_true", help="Delete smoke assets at end")
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path("app/test_scripts/render_things/svg_library_smoke_report.json"),
        help="Write test report JSON here",
    )
    args = parser.parse_args()

    local_report = run_local_validation(count=args.count, seed=args.seed)
    report: dict[str, Any] = {"local_validation": local_report}

    if args.post:
        report["api_smoke"] = run_api_smoke(
            count=args.count,
            seed=args.seed,
            create_count=max(1, args.create_count),
            cleanup=args.cleanup,
        )

    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nReport written to: {args.report_out}")

    local_failures = report["local_validation"]["failure_count"]
    api_failures = report.get("api_smoke", {}).get("failure_count", 0)
    return 0 if (local_failures + api_failures) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

