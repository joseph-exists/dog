#!/usr/bin/env python3
"""Batch runner for graph_routing_showcase.py."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_SCENARIOS = ["balanced", "hotspot_h", "cross_region", "downstream_pressure"]
DEFAULT_POLICIES = ["baseline", "stability", "throughput"]
DEFAULT_MODES = ["straight", "curved", "orthogonal", "bundled"]
DEFAULT_TOPOLOGIES = ["default", "sparse", "dense", "clustered"]


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
    p = argparse.ArgumentParser(description="Batch runner for graph routing strategy comparison.")
    p.add_argument("--scenarios", type=str, default="all", help="Comma list or 'all'.")
    p.add_argument("--policies", type=str, default="all", help="Comma list or 'all'.")
    p.add_argument("--modes", type=str, default="all", help="Comma list or 'all'.")
    p.add_argument("--topologies", type=str, default="all", help="Comma list or 'all'.")
    p.add_argument("--repeats", type=int, default=1, help="Runs per scenario/policy/mode tuple.")
    p.add_argument("--seed-start", type=int, default=251, help="Initial seed.")
    p.add_argument("--seed-step", type=int, default=19, help="Seed increment per repeat.")

    p.add_argument("--duration", type=float, default=6.0, help="Forwarded duration.")
    p.add_argument("--dt", type=float, default=0.03, help="Forwarded simulation step.")
    p.add_argument("--fps", type=int, default=16, help="Forwarded render FPS.")
    p.add_argument(
        "--camera-mode",
        choices=["fixed", "track", "hybrid"],
        default="fixed",
        help="Forwarded camera mode.",
    )
    p.add_argument("--packet-rate", type=float, default=1.6, help="Forwarded packet spawn rate.")
    p.add_argument("--packets-max", type=int, default=520, help="Forwarded packet limit.")
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
        default="graph_routing_showcase_comparison",
        help="Output directory for leaderboard/reports.",
    )
    p.add_argument("--csv-name", type=str, default="leaderboard.csv", help="Leaderboard CSV file name.")
    p.add_argument("--json-name", type=str, default="leaderboard.json", help="Leaderboard JSON file name.")
    p.add_argument("--fail-fast", action="store_true", help="Stop on first failed run.")
    return p.parse_args()


def flatten_report(report: dict) -> dict:
    metrics = report.get("metrics", {})
    mode_metrics = metrics.get("modes", {})

    # Runner executes single mode runs, so exactly one key is expected.
    mode = report.get("mode", "")
    mm = mode_metrics.get(mode, {})

    return {
        "scenario": report.get("scenario", ""),
        "policy": report.get("policy", ""),
        "topology": report.get("topology", ""),
        "mode": mode,
        "seed": int(report.get("seed", 0)),
        "duration": float(report.get("duration", 0.0)),
        "dt": float(report.get("dt", 0.0)),
        "fps": int(report.get("fps", 0)),
        "camera_mode": report.get("camera_mode", ""),
        "score": float(mm.get("score", metrics.get("score", 0.0))),
        "crossings": int(mm.get("crossings", metrics.get("crossings", 0))),
        "avg_bends": float(mm.get("avg_bends", metrics.get("avg_bends", 0.0))),
        "ink": float(mm.get("ink", metrics.get("ink", 0.0))),
        "packets_spawned": int(mm.get("packets_spawned", metrics.get("packets_spawned", 0))),
        "total_visible_packets": int(metrics.get("total_visible_packets", 0)),
    }


def main() -> int:
    args = parse_args()

    try:
        scenarios = parse_csv_list(args.scenarios, allowed=DEFAULT_SCENARIOS)
        policies = parse_csv_list(args.policies, allowed=DEFAULT_POLICIES)
        modes = parse_csv_list(args.modes, allowed=DEFAULT_MODES)
        topologies = parse_csv_list(args.topologies, allowed=DEFAULT_TOPOLOGIES)
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

    target_script = Path(__file__).with_name("graph_routing_showcase.py")
    if not target_script.exists():
        print(f"❌ Missing companion script: {target_script}")
        return 2

    rows: list[dict] = []
    failures: list[tuple[str, int]] = []

    total_runs = len(scenarios) * len(policies) * len(topologies) * len(modes) * repeats
    run_idx = 0

    for scenario in scenarios:
        for policy in policies:
            for topology in topologies:
                for mode in modes:
                    for rep in range(repeats):
                        run_idx += 1
                        seed = args.seed_start + rep * args.seed_step
                        run_id = f"{scenario}__{policy}__{topology}__{mode}__seed{seed}__r{rep+1}"
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
                            "--topology",
                            topology,
                            "--mode",
                            mode,
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
                            "--packet-rate",
                            str(args.packet_rate),
                            "--packets-max",
                            str(args.packets_max),
                            "--format",
                            args.format,
                            "--output",
                            str(media_path),
                            "--report-json",
                            str(report_path),
                        ]

                        print(
                            f"[{run_idx:03d}/{total_runs:03d}] scenario={scenario} policy={policy} "
                            f"topology={topology} mode={mode} repeat={rep+1}/{repeats} seed={seed}"
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
                            f"   score={row['score']:.3f} crossings={row['crossings']} "
                            f"avg_bends={row['avg_bends']:.2f} packets={row['packets_spawned']}"
                        )

                    if args.fail_fast and failures:
                        break
                if args.fail_fast and failures:
                    break
            if args.fail_fast and failures:
                break
        if args.fail_fast and failures:
            break

    if not rows:
        print("❌ No successful runs. Nothing to rank.")
        return 1

    rows.sort(
        key=lambda r: (
            -r["score"],
            r["crossings"],
            r["avg_bends"],
            r["ink"],
            -r["packets_spawned"],
            r["scenario"],
            r["policy"],
            r["topology"],
            r["mode"],
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
        "topology",
        "mode",
        "seed",
        "score",
        "crossings",
        "avg_bends",
        "ink",
        "packets_spawned",
        "total_visible_packets",
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
        "topologies": topologies,
        "modes": modes,
        "repeats": repeats,
        "top_run": rows[0],
        "runs": rows,
        "failures": [{"run_id": rid, "code": code} for rid, code in failures],
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\n✅ Leaderboard CSV: {csv_path}")
    print(f"✅ Leaderboard JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
