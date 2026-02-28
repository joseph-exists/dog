#!/usr/bin/env python3
"""Run renderable examples into one directory for UX review."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Entry:
    path: Path
    kind: str


def parse_manifest(path: Path) -> list[Entry]:
    entries: list[Entry] = []
    current_path: Path | None = None
    current_kind: str | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- path:"):
            if current_path is not None and current_kind is not None:
                entries.append(Entry(path=current_path, kind=current_kind))
            current_path = Path(line.split(":", 1)[1].strip())
            current_kind = None
            continue
        if line.startswith("kind:") and current_path is not None:
            current_kind = line.split(":", 1)[1].strip()

    if current_path is not None and current_kind is not None:
        entries.append(Entry(path=current_path, kind=current_kind))
    return entries


def script_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def supports_flag(text: str, flag: str) -> bool:
    return f'"{flag}"' in text or f"'{flag}'" in text


def default_ext(kind: str) -> str:
    if kind == "animation":
        return "gif"
    if kind == "static":
        return "svg"
    return "txt"


def build_cmd(
    python_bin: str,
    repo_root: Path,
    entry: Entry,
    output_dir: Path,
    fast: bool,
) -> list[str]:
    script_abs = repo_root / entry.path
    txt = script_text(script_abs)
    cmd = [python_bin, str(script_abs)]

    if supports_flag(txt, "--output-prefix"):
        cmd.extend(["--output-prefix", str(output_dir / script_abs.stem)])
    elif supports_flag(txt, "--output"):
        ext = default_ext(entry.kind)
        cmd.extend(["--output", str(output_dir / f"{script_abs.stem}.{ext}")])

    if supports_flag(txt, "--format"):
        if entry.kind == "animation":
            cmd.extend(["--format", "gif"])
        elif entry.kind == "static":
            cmd.extend(["--format", "svg"])

    if fast and entry.kind == "animation":
        if supports_flag(txt, "--duration"):
            cmd.extend(["--duration", "4"])
        if supports_flag(txt, "--fps"):
            cmd.extend(["--fps", "12"])

    return cmd


def write_index(output_dir: Path) -> None:
    media = sorted(
        [p for p in output_dir.rglob("*") if p.suffix.lower() in {".svg", ".gif", ".mp4", ".png", ".pdf", ".ps"}]
    )
    lines = ["# UX Review Output Index", ""]
    for p in media:
        lines.append(f"- `{p.relative_to(output_dir)}`")
    lines.append("")
    (output_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run renderable examples into one UX review directory.")
    p.add_argument("--output-dir", type=str, default="examples-other/review_outputs/full_suite")
    p.add_argument("--manifest", type=str, default="examples-other/examples_manifest.yaml")
    p.add_argument("--python", type=str, default=sys.executable)
    p.add_argument("--fast", action="store_true", help="Lower animation duration/fps for quicker runs.")
    p.add_argument("--stop-on-fail", action="store_true")
    p.add_argument("--include-utility", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = parse_manifest((repo_root / args.manifest).resolve())
    selected = [
        e
        for e in entries
        if e.kind in {"static", "animation"} or (args.include_utility and e.kind == "utility")
    ]

    results: list[dict[str, str | int]] = []
    for e in selected:
        cmd = build_cmd(args.python, repo_root, e, output_dir, args.fast)
        proc = subprocess.run(
            cmd,
            cwd=output_dir,
            text=True,
            capture_output=True,
        )
        status = "ok" if proc.returncode == 0 else "fail"
        results.append(
            {
                "script": str(e.path),
                "kind": e.kind,
                "status": status,
                "returncode": proc.returncode,
                "command": " ".join(cmd),
            }
        )
        if proc.stdout:
            (output_dir / f"{Path(e.path).stem}.stdout.log").write_text(proc.stdout, encoding="utf-8")
        if proc.stderr:
            (output_dir / f"{Path(e.path).stem}.stderr.log").write_text(proc.stderr, encoding="utf-8")

        print(f"[{status}] {e.path}")
        if proc.returncode != 0 and args.stop_on_fail:
            break

    summary = {
        "output_dir": str(output_dir),
        "total": len(results),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "results": results,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_index(output_dir)
    print(f"summary={output_dir / 'summary.json'}")
    print(f"index={output_dir / 'index.md'}")
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
