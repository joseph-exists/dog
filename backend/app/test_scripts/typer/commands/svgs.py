"""
SVG Library Commands

Typer command suite for the `/svgs` API, including deterministic
combinatorics-based generation workflows to populate a large SVG library.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from auth_helper import get_authenticated_session

# Render engine lives in Tesser
_TESSER_SRC = Path(__file__).resolve().parents[5] / "tesser" / "src"
if str(_TESSER_SRC) not in sys.path:
    sys.path.insert(0, str(_TESSER_SRC))

from tesserax_service.scripts.svg_compose import (  # noqa: E402
    INPUT_SCHEMA,
    RINGS_INPUT_SCHEMA,
    SOFT_GRADIENT_INPUT_SCHEMA,
    render_svg,
    validate_svg,
)

# Planner stays in render_things
RENDER_THINGS_DIR = Path(__file__).resolve().parents[2] / "render_things"
if str(RENDER_THINGS_DIR) not in sys.path:
    sys.path.append(str(RENDER_THINGS_DIR))

from svg_library_tools import build_asset_metadata, build_generation_plan  # noqa: E402

app = typer.Typer(help="SVG library management and generation commands", no_args_is_help=True)

from cli_config import get_api_v1_url

BASE_URL = get_api_v1_url()


def _get_session():
    try:
        return get_authenticated_session()
    except Exception as exc:  # pragma: no cover - CLI path
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


def _json_loads_or_exit(raw: str, *, label: str) -> dict[str, Any]:
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        typer.secho(f"❌ Invalid JSON for {label}: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    if not isinstance(obj, dict):
        typer.secho(f"❌ {label} must be a JSON object", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    return obj


@app.command("list")
def list_svgs(
    limit: Annotated[int, typer.Option(help="Maximum assets to list")] = 50,
    skip: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    visibility: Annotated[
        str | None,
        typer.Option("--visibility", help="Filter: private or public"),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """List SVG assets for the current authenticated user."""
    params: dict[str, Any] = {"limit": limit, "skip": skip}
    if visibility:
        params["visibility"] = visibility

    session = _get_session()
    resp = session.get(f"{BASE_URL}/svgs", params=params)
    if resp.status_code != 200:
        typer.secho("❌ Failed to list SVG assets", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {resp.status_code}")
        typer.echo(resp.text)
        raise typer.Exit(1)

    payload = resp.json()
    rows = payload.get("data", [])
    if json_output:
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.echo(f"\n🧩 SVG assets ({len(rows)} of {payload.get('count', len(rows))}):\n")
    if not rows:
        typer.secho("  No assets found", fg=typer.colors.YELLOW)
        return
    for row in rows:
        typer.secho(f"  • {row.get('name', 'unnamed')}", fg=typer.colors.CYAN)
        typer.echo(f"    ID: {row.get('id')}")
        typer.echo(f"    Visibility: {row.get('visibility')}")
        if row.get("source_private_id"):
            typer.echo(f"    Source: {row['source_private_id']}")
        typer.echo()


@app.command("get")
def get_svg(
    svg_id: Annotated[str, typer.Argument(help="SVG asset UUID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Get one SVG asset by ID."""
    session = _get_session()
    resp = session.get(f"{BASE_URL}/svgs/{svg_id}")
    if resp.status_code != 200:
        typer.secho(f"❌ Failed to get SVG asset {svg_id}", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {resp.status_code}")
        typer.echo(resp.text)
        raise typer.Exit(1)

    row = resp.json()
    if json_output:
        typer.echo(json.dumps(row, indent=2))
        return

    typer.secho(f"\n✅ SVG asset: {row.get('name', 'unnamed')}", fg=typer.colors.GREEN)
    typer.echo(f"ID: {row.get('id')}")
    typer.echo(f"Visibility: {row.get('visibility')}")
    typer.echo(f"Updated: {row.get('updated_at')}")
    typer.echo(f"Bytes: {len((row.get('svg_markup') or '').encode('utf-8'))}")


@app.command("create-private")
def create_private(
    name: Annotated[str, typer.Argument(help="Asset display name")],
    svg_file: Annotated[Path | None, typer.Option("--svg-file", help="Path to SVG file")] = None,
    svg_inline: Annotated[str | None, typer.Option("--svg", help="Inline SVG markup")] = None,
    description: Annotated[str, typer.Option("--desc", "-d", help="Asset description")] = "",
    metadata_json: Annotated[
        str | None,
        typer.Option("--metadata", help="JSON object string for metadata_json"),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Create a private SVG asset from file or inline markup."""
    if bool(svg_file) == bool(svg_inline):
        typer.secho("❌ Provide exactly one of --svg-file or --svg", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    svg_markup = svg_inline
    if svg_file:
        if not svg_file.exists():
            typer.secho(f"❌ SVG file not found: {svg_file}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        svg_markup = svg_file.read_text(encoding="utf-8")

    assert isinstance(svg_markup, str)
    metadata: dict[str, Any] = {}
    if metadata_json:
        metadata = _json_loads_or_exit(metadata_json, label="metadata")

    payload = {
        "visibility": "private",
        "name": name,
        "description": description or None,
        "svg_markup": svg_markup,
        "metadata_json": metadata,
    }
    session = _get_session()
    resp = session.post(f"{BASE_URL}/svgs", json=payload)
    if resp.status_code not in (200, 201):
        typer.secho("❌ Failed to create private SVG", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {resp.status_code}")
        typer.echo(resp.text)
        raise typer.Exit(1)

    row = resp.json()
    if json_output:
        typer.echo(json.dumps(row, indent=2))
        return
    typer.secho("✅ Private SVG created", fg=typer.colors.GREEN)
    typer.echo(f"ID: {row.get('id')}")
    typer.echo(f"Name: {row.get('name')}")


@app.command("copy-public")
def copy_public(
    source_private_id: Annotated[str, typer.Argument(help="Source private asset UUID")],
    name: Annotated[str | None, typer.Option("--name", help="Override display name")] = None,
    description: Annotated[str | None, typer.Option("--desc", help="Override description")] = None,
    metadata_json: Annotated[str | None, typer.Option("--metadata", help="Metadata override JSON")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Create a public copy from an existing private asset."""
    payload: dict[str, Any] = {
        "visibility": "public",
        "source_private_id": source_private_id,
    }
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if metadata_json is not None:
        payload["metadata_json"] = _json_loads_or_exit(metadata_json, label="metadata")

    session = _get_session()
    resp = session.post(f"{BASE_URL}/svgs", json=payload)
    if resp.status_code not in (200, 201):
        typer.secho("❌ Failed to create public copy", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {resp.status_code}")
        typer.echo(resp.text)
        raise typer.Exit(1)

    row = resp.json()
    if json_output:
        typer.echo(json.dumps(row, indent=2))
        return
    typer.secho("✅ Public copy created", fg=typer.colors.GREEN)
    typer.echo(f"ID: {row.get('id')}")
    typer.echo(f"Source: {row.get('source_private_id')}")


@app.command("patch")
def patch_svg(
    svg_id: Annotated[str, typer.Argument(help="SVG asset UUID to patch")],
    name: Annotated[str | None, typer.Option("--name", help="Set name")] = None,
    description: Annotated[str | None, typer.Option("--desc", help="Set description")] = None,
    visibility: Annotated[str | None, typer.Option("--visibility", help="Set visibility")] = None,
    source_private_id: Annotated[str | None, typer.Option("--source-private-id")] = None,
    svg_file: Annotated[Path | None, typer.Option("--svg-file", help="Replace markup from file")] = None,
    metadata_json: Annotated[str | None, typer.Option("--metadata", help="Set metadata JSON object")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output raw JSON")] = False,
) -> None:
    """Patch an SVG asset with partial fields."""
    payload: dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if visibility is not None:
        payload["visibility"] = visibility
    if source_private_id is not None:
        payload["source_private_id"] = source_private_id
    if svg_file is not None:
        if not svg_file.exists():
            typer.secho(f"❌ SVG file not found: {svg_file}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        payload["svg_markup"] = svg_file.read_text(encoding="utf-8")
    if metadata_json is not None:
        payload["metadata_json"] = _json_loads_or_exit(metadata_json, label="metadata")

    if not payload:
        typer.secho("❌ No patch fields provided", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    session = _get_session()
    resp = session.patch(f"{BASE_URL}/svgs/{svg_id}", json=payload)
    if resp.status_code != 200:
        typer.secho("❌ Failed to patch SVG asset", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {resp.status_code}")
        typer.echo(resp.text)
        raise typer.Exit(1)

    row = resp.json()
    if json_output:
        typer.echo(json.dumps(row, indent=2))
        return
    typer.secho("✅ SVG patched", fg=typer.colors.GREEN)
    typer.echo(f"ID: {row.get('id')}")
    typer.echo(f"Visibility: {row.get('visibility')}")


@app.command("delete")
def delete_svg(
    svg_id: Annotated[str, typer.Argument(help="SVG asset UUID to delete")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
) -> None:
    """Delete one SVG asset."""
    if not force:
        typer.secho(f"⚠️  Delete SVG asset {svg_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Continue?"):
            raise typer.Exit(0)

    session = _get_session()
    resp = session.delete(f"{BASE_URL}/svgs/{svg_id}")
    if resp.status_code not in (200, 204):
        typer.secho("❌ Failed to delete SVG asset", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {resp.status_code}")
        typer.echo(resp.text)
        raise typer.Exit(1)
    typer.secho("✅ SVG deleted", fg=typer.colors.GREEN)


@app.command("plan")
def plan_generation(
    count: Annotated[int, typer.Option("--count", "-n", help="Number of scenarios")] = 120,
    seed: Annotated[int, typer.Option("--seed", help="Deterministic planner seed")] = 20260315,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output JSON plan path"),
    ] = Path("app/test_scripts/render_things/svg_library_plan.json"),
    include_svg_preview: Annotated[
        int,
        typer.Option("--preview", help="Embed first N rendered SVGs in plan for inspection"),
    ] = 0,
) -> None:
    """
    Build a deterministic generation plan from combinatoric domains.
    """
    plan = build_generation_plan(total_count=count, seed=seed)
    if include_svg_preview > 0:
        preview_rows = plan.get("rows", [])[:include_svg_preview]
        for row in preview_rows:
            row["svg_preview"] = render_svg(row)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    typer.secho("✅ Generation plan written", fg=typer.colors.GREEN)
    typer.echo(f"Path: {output}")
    typer.echo(
        f"Pairwise coverage: {plan['meta'].get('pairwise_coverage_pct', 'n/a')}% "
        f"for {plan['meta'].get('pairwise_count')} core rows"
    )


@app.command("seed")
def seed_library(
    count: Annotated[int, typer.Option("--count", "-n", help="Asset count when generating a new plan")] = 120,
    seed: Annotated[int, typer.Option("--seed", help="Deterministic generation seed")] = 20260315,
    plan_file: Annotated[
        Path | None,
        typer.Option("--plan", help="Optional plan JSON path generated via `svgs plan`"),
    ] = None,
    name_prefix: Annotated[str, typer.Option("--name-prefix", help="Asset name prefix")] = "svg-lib",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Generate and validate only; do not POST")] = False,
    public_copy_ratio: Annotated[
        float,
        typer.Option(
            "--public-copy-ratio",
            help="Fraction of created private assets to mirror as public copies",
            min=0.0,
            max=1.0,
        ),
    ] = 0.10,
    output_manifest: Annotated[
        Path,
        typer.Option("--manifest-out", help="Write run manifest/report"),
    ] = Path("app/test_scripts/render_things/svg_library_seed_report.json"),
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """
    Populate the SVG library using generated scenarios and deterministic rendering.
    """

    def log(msg: str) -> None:
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    if plan_file is not None:
        if not plan_file.exists():
            typer.secho(f"❌ Plan file not found: {plan_file}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
    else:
        plan = build_generation_plan(total_count=count, seed=seed)

    rows = plan.get("rows", [])
    if not rows:
        typer.secho("❌ No rows in plan", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    created_private_ids: list[str] = []
    created_public_ids: list[str] = []
    failed: list[dict[str, Any]] = []
    session = None if dry_run else _get_session()

    for row in rows:
        scenario_id = row.get("scenario_id", "unknown")
        svg_markup = render_svg(row)
        errors = validate_svg(svg_markup)
        if errors:
            failed.append({"scenario_id": scenario_id, "stage": "validate", "errors": errors})
            log(f"Validation failed for {scenario_id}: {errors}")
            continue

        payload = {
            "visibility": "private",
            "name": f"{name_prefix}-{scenario_id}",
            "description": (
                f"{row.get('generation_tier')} | family={row.get('style_family')} | "
                f"seed={row.get('scenario_seed')}"
            ),
            "svg_markup": svg_markup,
            "metadata_json": build_asset_metadata(row, svg_markup),
        }

        if dry_run:
            log(f"[dry-run] would create: {payload['name']}")
            continue

        assert session is not None
        response = session.post(f"{BASE_URL}/svgs", json=payload)
        if response.status_code not in (200, 201):
            failed.append(
                {
                    "scenario_id": scenario_id,
                    "stage": "create-private",
                    "status": response.status_code,
                    "body": response.text[:600],
                }
            )
            continue

        body = response.json()
        if body.get("id"):
            created_private_ids.append(str(body["id"]))

    if not dry_run and created_private_ids and public_copy_ratio > 0:
        target = int(len(created_private_ids) * public_copy_ratio)
        for source_id in created_private_ids[:target]:
            payload = {
                "visibility": "public",
                "source_private_id": source_id,
                "name": f"{name_prefix}-public-{source_id[:8]}",
                "description": "Public mirror generated by svgs seed command",
            }
            assert session is not None
            response = session.post(f"{BASE_URL}/svgs", json=payload)
            if response.status_code not in (200, 201):
                failed.append(
                    {
                        "source_private_id": source_id,
                        "stage": "create-public-copy",
                        "status": response.status_code,
                        "body": response.text[:600],
                    }
                )
                continue
            body = response.json()
            if body.get("id"):
                created_public_ids.append(str(body["id"]))

    report = {
        "meta": plan.get("meta", {}),
        "dry_run": dry_run,
        "attempted": len(rows),
        "created_private_count": len(created_private_ids),
        "created_public_count": len(created_public_ids),
        "failed_count": len(failed),
        "created_private_ids": created_private_ids,
        "created_public_ids": created_public_ids,
        "failed": failed,
    }
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if dry_run:
        typer.secho("✅ Dry run complete", fg=typer.colors.GREEN)
    else:
        typer.secho("✅ Seeding run complete", fg=typer.colors.GREEN)
    typer.echo(f"Report: {output_manifest}")
    typer.echo(f"Created private: {len(created_private_ids)}")
    typer.echo(f"Created public: {len(created_public_ids)}")
    typer.echo(f"Failed: {len(failed)}")

    if failed:
        raise typer.Exit(2)


@app.command("knobs")
def list_knobs(
    script: Annotated[
        str,
        typer.Option("--script", "-s", help="Script to inspect (default: svg.compose)"),
    ] = "svg.compose",
) -> None:
    """List all available knobs and their valid values for a script."""
    schema_map = {
        "svg.compose":        INPUT_SCHEMA,
        "svg.vector-rings":   RINGS_INPUT_SCHEMA,
        "svg.soft-gradient":  SOFT_GRADIENT_INPUT_SCHEMA,
    }
    schema = schema_map.get(script)
    if schema is None:
        typer.secho(
            f"❌ Unknown script: {script}. Known: {', '.join(schema_map)}",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(1)

    typer.echo(f"\n🎛  Knobs for {script}:\n")
    for knob, spec in schema.get("properties", {}).items():
        enum_vals = spec.get("enum", [])
        default   = spec.get("default", "")
        desc      = spec.get("description", "")
        if enum_vals:
            vals_str = " | ".join(str(v) for v in enum_vals)
            typer.secho(f"  {knob}", fg=typer.colors.CYAN, nl=False)
            typer.echo(f"  [{vals_str}]  default={default}")
        else:
            typer.secho(f"  {knob}", fg=typer.colors.CYAN, nl=False)
            typer.echo(f"  {spec.get('type','')}  default={default}  {desc}")
    typer.echo()


@app.command("render")
def render_single(
    output: Annotated[Path, typer.Argument(help="Output .svg file path")],
    params_json: Annotated[
        str | None,
        typer.Option("--params", "-p", help="JSON object of knob overrides"),
    ] = None,
    seed: Annotated[int | None, typer.Option("--seed", help="Seed override")] = None,
    style_family: Annotated[str | None, typer.Option("--family", "-f")] = None,
    open_after: Annotated[bool, typer.Option("--open", help="Open in browser after render")] = False,
) -> None:
    """
    Render a single SVG to a local file with hand-picked knobs.

    Example:
      svgs render out.svg --family glitch --seed 99
      svgs render out.svg --params '{"palette_family":"neon","displacement_scale":"64"}'
    """
    params: dict[str, Any] = {}
    if params_json:
        params = _json_loads_or_exit(params_json, label="params")
    if seed is not None:
        params["seed"] = seed
    if style_family is not None:
        params["style_family"] = style_family

    svg = render_svg(params)
    errors = validate_svg(svg)
    if errors:
        typer.secho(f"❌ Render produced invalid SVG: {errors}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    typer.secho(f"✅ Rendered to {output}", fg=typer.colors.GREEN)
    typer.echo(f"   Bytes: {len(svg.encode('utf-8'))}")
    if open_after:
        import subprocess
        import platform
        opener = "open" if platform.system() == "Darwin" else "xdg-open"
        subprocess.Popen([opener, str(output)])


if __name__ == "__main__":
    app()

