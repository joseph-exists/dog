#!/usr/bin/env python3
"""Batch runner for animation_supply_chain_network_stress.py."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_SCENARIOS = ["port_delay", "lane_disruption", "demand_wave", "multi_shock"]
DEFAULT_POLICIES = ["lean", "balanced", "resilient"]


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
    p = argparse.ArgumentParser(description="Batch runner for supply-chain network stress comparison.")
    p.add_argument("--scenarios", type=str, default="all", help="Comma list or 'all'.")
    p.add_argument("--policies", type=str, default="all", help="Comma list or 'all'.")
    p.add_argument("--repeats", type=int, default=1, help="Runs per scenario/policy pair.")
    p.add_argument("--seed-start", type=int, default=193, help="Initial seed.")
    p.add_argument("--seed-step", type=int, default=29, help="Seed increment per repeat.")

    p.add_argument("--duration", type=float, default=6.0, help="Forwarded duration.")
    p.add_argument("--dt", type=float, default=0.03, help="Forwarded simulation step.")
    p.add_argument("--fps", type=int, default=16, help="Forwarded render FPS.")
    p.add_argument(
        "--camera-mode",
        choices=["fixed", "track", "hybrid"],
        default="hybrid",
        help="Forwarded camera mode.",
    )
    p.add_argument(
        "--format",
        choices=["gif", "mp4"],
        default="gif",
        help="Format for media when --save-media is enabled.",
    )

    p.add_argument("--save-media", action="store_true", help="Persist per-run media outputs.")
    p.add_argument(
        "--output-dir",
        type=str,
        default="supply_chain_network_stress_comparison",
        help="Output directory for leaderboard/reports.",
    )
    p.add_argument("--csv-name", type=str, default="leaderboard.csv", help="Leaderboard CSV file name.")
    p.add_argument("--json-name", type=str, default="leaderboard.json", help="Leaderboard JSON file name.")
    p.add_argument("--fail-fast", action="store_true", help="Stop on first failed run.")
    return p.parse_args()


def flatten_report(report: dict) -> dict:
    event = report.get("event", {})
    metrics = report.get("metrics", {})
    return {
        "scenario": report.get("scenario", ""),
        "policy": report.get("policy", ""),
        "seed": int(report.get("seed", 0)),
        "duration": float(report.get("duration", 0.0)),
        "dt": float(report.get("dt", 0.0)),
        "fps": int(report.get("fps", 0)),
        "camera_mode": report.get("camera_mode", ""),
        "severity": float(event.get("severity", 0.0)),
        "demand_spike_node": event.get("demand_spike_node", ""),
        "service_level": float(metrics.get("service_level", 0.0)),
        "peak_backlog": float(metrics.get("peak_backlog", 0.0)),
        "peak_route_overload": float(metrics.get("peak_route_overload", 0.0)),
        "reroute_utilization": float(metrics.get("reroute_utilization", 0.0)),
        "transitions": int(metrics.get("transitions", 0)),
        "visible_packets": int(metrics.get("visible_packets", 0)),
        "final_phase": metrics.get("final_phase", ""),
    }


def main() -> int:
    args = parse_args()

    try:
        scenarios = parse_csv_list(args.scenarios, allowed=DEFAULT_SCENARIOS)
        policies = parse_csv_list(args.policies, allowed=DEFAULT_POLICIES)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 2

    repeats = max(1, args.repeats)
    out_dir = Path(args.output_dir)
    reports_dir = out_dir / "reports"
    media_dir = out_dir / "media"
    scratch_dir = out_dir / ".scratch"
    reports_dir.mkdir(parents=True, exist_ok=True)
    if args.save_media:
        media_dir.mkdir(parents=True, exist_ok=True)
    else:
        scratch_dir.mkdir(parents=True, exist_ok=True)

    target_script = Path(__file__).with_name("animation_supply_chain_network_stress.py")
    if not target_script.exists():
        print(f"❌ Missing companion script: {target_script}")
        return 2

    rows: list[dict] = []
    failures: list[tuple[str, int]] = []

    total_runs = len(scenarios) * len(policies) * repeats
    run_idx = 0

    for scenario in scenarios:
        for policy in policies:
            for rep in range(repeats):
                run_idx += 1
                seed = args.seed_start + rep * args.seed_step
                run_id = f"{scenario}__{policy}__seed{seed}__r{rep+1}"
                report_path = reports_dir / f"{run_id}.json"
                media_parent = media_dir if args.save_media else scratch_dir
                media_path = media_parent / f"{run_id}.{args.format}"

                cmd = [
                    sys.executable,
                    str(target_script),
                    "--scenario",
                    scenario,
                    "--policy",
                    policy,
                    "--seed",
                    str(seed),
                    "--duration",
                    str(args.duration),
                    "--dt",
                    str(args.dt),
                    "--fps",
                    str(args.fps),
                    "--camera-mode",
                    args.camera_mode,
                    "--format",
                    args.format,
                    "--output",
                    str(media_path),
                    "--report-json",
                    str(report_path),
                ]

                print(
                    f"[{run_idx:02d}/{total_runs:02d}] scenario={scenario} policy={policy} "
                    f"repeat={rep+1}/{repeats} seed={seed}"
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
                    f"   service_level={row['service_level']:.3f} peak_backlog={row['peak_backlog']:.3f} "
                    f"peak_route_overload={row['peak_route_overload']:.3f} reroute_util={row['reroute_utilization']:.3f}"
                )

            if args.fail_fast and failures:
                break
        if args.fail_fast and failures:
            break

    if not rows:
        print("❌ No successful runs. Nothing to rank.")
        return 1

    rows.sort(
        key=lambda r: (
            -r["service_level"],
            r["peak_backlog"],
            r["peak_route_overload"],
            -r["reroute_utilization"],
            r["scenario"],
            r["policy"],
            r["seed"],
        )
    )
    for i, row in enumerate(rows, start=1):
        row["rank"] = i

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / args.csv_name
    json_path = out_dir / args.json_name

    fieldnames = [
        "rank",
        "scenario",
        "policy",
        "seed",
        "service_level",
        "peak_backlog",
        "peak_route_overload",
        "reroute_utilization",
        "severity",
        "demand_spike_node",
        "transitions",
        "visible_packets",
        "final_phase",
        "duration",
        "dt",
        "fps",
        "camera_mode",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    summary = {
        "total_requested_runs": total_runs,
        "successful_runs": len(rows),
        "failed_runs": len(failures),
        "scenarios": scenarios,
        "policies": policies,
        "repeats": repeats,
        "top_run": rows[0],
        "runs": rows,
        "failures": [{"run_id": rid, "code": code} for rid, code in failures],
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\n✅ Leaderboard CSV: {csv_path}")
    print(f"✅ Leaderboard JSON: {json_path}")
    print(
        f"   successful={len(rows)} failed={len(failures)} "
        f"best={rows[0]['scenario']}/{rows[0]['policy']} service_level={rows[0]['service_level']:.3f}"
    )
    return 0 if not failures else 3


if __name__ == "__main__":
    raise SystemExit(main())
