#!/usr/bin/env python3
"""Batch runner for animation_regression_suite.py."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_SCENARIOS = ["baseline", "stress", "recovery"]
DEFAULT_POLICIES = ["strict", "balanced", "throughput"]
DEFAULT_FIXTURES = ["pipeline", "ring", "mesh"]


def parse_csv_list(value: str, *, allowed: list[str], all_token: str = "all") -> list[str]:
    raw = [v.strip() for v in value.split(",") if v.strip()]
    if not raw:
        return list(allowed)
    if len(raw) == 1 and raw[0] == all_token:
        return list(allowed)
    bad = [v for v in raw if v not in allowed]
    if bad:
        raise ValueError(f"Unsupported entries: {', '.join(bad)}. Allowed: {', '.join(allowed)}")

    out: list[str] = []
    seen: set[str] = set()
    for v in raw:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch runner for deterministic animation regression suite.")
    p.add_argument("--scenarios", type=str, default="all", help="Comma list or 'all'.")
    p.add_argument("--policies", type=str, default="all", help="Comma list or 'all'.")
    p.add_argument("--fixtures", type=str, default="all", help="Comma list or 'all'.")
    p.add_argument("--repeats", type=int, default=2, help="Runs per scenario/policy/fixture tuple.")
    p.add_argument("--seed-start", type=int, default=311, help="Initial seed.")
    p.add_argument("--seed-step", type=int, default=0, help="Seed increment per repeat (0 for determinism checks).")

    p.add_argument("--duration", type=float, default=4.0)
    p.add_argument("--dt", type=float, default=0.03)
    p.add_argument("--fps", type=int, default=12)
    p.add_argument("--packet-rate", type=float, default=1.8)
    p.add_argument("--packets-max", type=int, default=420)
    p.add_argument("--hash-sample-step", type=int, default=1)

    p.add_argument(
        "--format",
        choices=["gif", "mp4"],
        default="gif",
        help="Format for media when --save-media is enabled.",
    )
    p.add_argument("--save-media", action="store_true", help="Persist per-run media outputs.")

    p.add_argument(
        "--baseline-dir",
        type=str,
        default="",
        help="Optional directory of reference signatures named <scenario>__<policy>__<fixture>.json",
    )
    p.add_argument(
        "--write-baseline",
        action="store_true",
        help="Write computed signatures to baseline dir using canonical names.",
    )
    p.add_argument("--overwrite-baseline", action="store_true", help="Overwrite existing baseline files.")

    p.add_argument(
        "--output-dir",
        type=str,
        default="animation_regression_suite_comparison",
        help="Output directory for leaderboard/reports.",
    )
    p.add_argument("--csv-name", type=str, default="leaderboard.csv")
    p.add_argument("--json-name", type=str, default="leaderboard.json")
    p.add_argument("--fail-fast", action="store_true", help="Stop on first failed run.")
    return p.parse_args()


def flatten_report(report: dict) -> dict:
    metrics = report.get("metrics", {})
    signature = metrics.get("signature", {})
    return {
        "scenario": report.get("scenario", ""),
        "policy": report.get("policy", ""),
        "fixture": report.get("fixture", ""),
        "seed": int(report.get("seed", 0)),
        "duration": float(report.get("duration", 0.0)),
        "dt": float(report.get("dt", 0.0)),
        "fps": int(report.get("fps", 0)),
        "status": metrics.get("status", ""),
        "mismatch_count": int(metrics.get("mismatch_count", 0)),
        "node_count": int(metrics.get("node_count", 0)),
        "edge_count": int(metrics.get("edge_count", 0)),
        "visible_packets": int(metrics.get("visible_packets", 0)),
        "frame_count": int(signature.get("frame_count", 0)),
        "sample_step": int(signature.get("sample_step", 0)),
        "combined_hash": signature.get("combined_hash", ""),
        "first_hash": signature.get("first_hash", ""),
        "mid_hash": signature.get("mid_hash", ""),
        "last_hash": signature.get("last_hash", ""),
    }


def baseline_path(baseline_dir: Path, scenario: str, policy: str, fixture: str) -> Path:
    return baseline_dir / f"{scenario}__{policy}__{fixture}.json"


def main() -> int:
    args = parse_args()

    try:
        scenarios = parse_csv_list(args.scenarios, allowed=DEFAULT_SCENARIOS)
        policies = parse_csv_list(args.policies, allowed=DEFAULT_POLICIES)
        fixtures = parse_csv_list(args.fixtures, allowed=DEFAULT_FIXTURES)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 2

    repeats = max(1, args.repeats)
    out_dir = Path(args.output_dir)
    reports_dir = out_dir / "reports"
    media_dir = out_dir / "media"
    scratch_dir = out_dir / ".scratch"
    baseline_dir = Path(args.baseline_dir) if args.baseline_dir else None

    reports_dir.mkdir(parents=True, exist_ok=True)
    if args.save_media:
        media_dir.mkdir(parents=True, exist_ok=True)
    else:
        scratch_dir.mkdir(parents=True, exist_ok=True)
    if args.write_baseline:
        if baseline_dir is None:
            baseline_dir = out_dir / "baseline"
        baseline_dir.mkdir(parents=True, exist_ok=True)

    target_script = Path(__file__).with_name("animation_regression_suite.py")
    if not target_script.exists():
        print(f"❌ Missing companion script: {target_script}")
        return 2

    rows: list[dict] = []
    failures: list[tuple[str, int]] = []

    total_runs = len(scenarios) * len(policies) * len(fixtures) * repeats
    run_idx = 0

    for scenario in scenarios:
        for policy in policies:
            for fixture in fixtures:
                for rep in range(repeats):
                    run_idx += 1
                    seed = args.seed_start + rep * args.seed_step
                    run_id = f"{scenario}__{policy}__{fixture}__seed{seed}__r{rep+1}"
                    report_path = reports_dir / f"{run_id}.json"
                    media_parent = media_dir if args.save_media else scratch_dir
                    media_path = media_parent / f"{run_id}.{args.format}"

                    ref_path = ""
                    if baseline_dir is not None:
                        cand = baseline_path(baseline_dir, scenario, policy, fixture)
                        if cand.exists():
                            ref_path = str(cand)

                    cmd = [
                        sys.executable,
                        str(target_script),
                        "--scenario",
                        scenario,
                        "--policy",
                        policy,
                        "--fixture",
                        fixture,
                        "--seed",
                        str(seed),
                        "--duration",
                        str(args.duration),
                        "--dt",
                        str(args.dt),
                        "--fps",
                        str(args.fps),
                        "--packet-rate",
                        str(args.packet_rate),
                        "--packets-max",
                        str(args.packets_max),
                        "--hash-sample-step",
                        str(args.hash_sample_step),
                        "--format",
                        args.format,
                        "--output",
                        str(media_path),
                        "--report-json",
                        str(report_path),
                    ]
                    if args.save_media:
                        cmd.append("--save-media")
                    if ref_path:
                        cmd.extend(["--signature-ref", ref_path])

                    print(
                        f"[{run_idx:03d}/{total_runs:03d}] scenario={scenario} policy={policy} "
                        f"fixture={fixture} repeat={rep+1}/{repeats} seed={seed}"
                    )
                    proc = subprocess.run(cmd, capture_output=True, text=True)
                    if proc.returncode != 0:
                        failures.append((run_id, proc.returncode))
                        print(f"   ❌ failed ({proc.returncode})")
                        if proc.stderr.strip():
                            print(proc.stderr.strip().splitlines()[-1])
                        if args.fail_fast:
                            break
                        continue

                    if not report_path.exists():
                        failures.append((run_id, 99))
                        print("   ❌ missing report_json output")
                        if args.fail_fast:
                            break
                        continue

                    report = json.loads(report_path.read_text(encoding="utf-8"))
                    row = flatten_report(report)
                    rows.append(row)
                    print(
                        f"   status={row['status']} mismatch={row['mismatch_count']} "
                        f"hash={row['combined_hash'][:12]} packets={row['visible_packets']}"
                    )

                    if args.write_baseline and baseline_dir is not None:
                        bpath = baseline_path(baseline_dir, scenario, policy, fixture)
                        if args.overwrite_baseline or not bpath.exists():
                            signature = report.get("metrics", {}).get("signature", {})
                            bpath.write_text(json.dumps(signature, indent=2), encoding="utf-8")

                if args.fail_fast and failures:
                    break
            if args.fail_fast and failures:
                break
        if args.fail_fast and failures:
            break

    if not rows:
        print("❌ No successful runs. Nothing to rank.")
        return 1

    # Group-level determinism checks across repeats.
    groups: dict[tuple[str, str, str], set[str]] = {}
    for row in rows:
        key = (row["scenario"], row["policy"], row["fixture"])
        groups.setdefault(key, set()).add(row["combined_hash"])

    for row in rows:
        key = (row["scenario"], row["policy"], row["fixture"])
        unique_hashes = len(groups.get(key, set()))
        row["repeat_unique_hashes"] = unique_hashes
        row["repeat_stable"] = 1 if unique_hashes == 1 else 0

    rows.sort(
        key=lambda r: (
            0 if r["status"] == "pass" else 1,
            0 if r["repeat_stable"] == 1 else 1,
            r["mismatch_count"],
            -r["visible_packets"],
            r["scenario"],
            r["policy"],
            r["fixture"],
            r["seed"],
        )
    )
    for i, row in enumerate(rows, start=1):
        row["rank"] = i

    csv_path = out_dir / args.csv_name
    json_path = out_dir / args.json_name

    fieldnames = [
        "rank",
        "scenario",
        "policy",
        "fixture",
        "seed",
        "status",
        "mismatch_count",
        "repeat_stable",
        "repeat_unique_hashes",
        "combined_hash",
        "frame_count",
        "sample_step",
        "visible_packets",
        "node_count",
        "edge_count",
        "duration",
        "dt",
        "fps",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    unstable_groups = [
        {"scenario": s, "policy": p, "fixture": f, "unique_hashes": len(h)}
        for (s, p, f), h in groups.items()
        if len(h) > 1
    ]

    summary = {
        "total_requested_runs": total_runs,
        "successful_runs": len(rows),
        "failed_runs": len(failures),
        "scenarios": scenarios,
        "policies": policies,
        "fixtures": fixtures,
        "repeats": repeats,
        "seed_start": args.seed_start,
        "seed_step": args.seed_step,
        "top_run": rows[0],
        "unstable_groups": unstable_groups,
        "runs": rows,
        "failures": [{"run_id": rid, "code": code} for rid, code in failures],
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\n✅ Leaderboard CSV: {csv_path}")
    print(f"✅ Leaderboard JSON: {json_path}")
    if baseline_dir is not None:
        print(f"✅ Baseline dir: {baseline_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
