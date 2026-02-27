#!/usr/bin/env python3
"""Convert wide tables into long-format rows for tufte_small_multiples_extended.py."""

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert wide-format CSV/JSON tables to long-format Tufte schema."
    )
    p.add_argument("--input", required=True, help="Input file path (.csv or .json).")
    p.add_argument("--output", required=True, help="Output file path (.csv or .json).")
    p.add_argument(
        "--input-format",
        choices=["csv", "json", "auto"],
        default="auto",
        help="Input format. Defaults to extension-based detection.",
    )
    p.add_argument(
        "--output-format",
        choices=["csv", "json", "auto"],
        default="auto",
        help="Output format. Defaults to extension-based detection.",
    )
    p.add_argument("--panel-col", default="panel", help="Panel column name in wide data.")
    p.add_argument("--cohort-col", default="cohort", help="Cohort column name in wide data.")
    p.add_argument(
        "--wide-mode",
        choices=["row", "grouped"],
        default="row",
        help=(
            "row: one panel per row with multiple time columns. "
            "grouped: multiple panels encoded as grouped columns (e.g., Revenue_t0)."
        ),
    )
    p.add_argument(
        "--time-columns",
        default="",
        help="Comma-separated explicit time columns. If omitted, columns are inferred.",
    )
    p.add_argument(
        "--exclude-columns",
        default="",
        help="Comma-separated columns to ignore during inference.",
    )
    p.add_argument(
        "--time-regex",
        default=r"^(t?\d+(\.\d+)?)$",
        help="Regex for inferring time value columns when --time-columns is omitted.",
    )
    p.add_argument(
        "--panel-time-regex",
        default=r"^(?P<panel>.+)_(?P<time>t?\d+(?:\.\d+)?)$",
        help=(
            "Regex for grouped mode with named groups 'panel' and 'time'. "
            "Example: Revenue_t0 -> panel=Revenue, time=t0."
        ),
    )
    p.add_argument(
        "--default-panel",
        default="Panel",
        help="Default panel label if panel column is missing.",
    )
    p.add_argument(
        "--default-cohort",
        default="C1",
        help="Default cohort label if cohort column is missing.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Fail if no time columns are inferred.",
    )
    return p.parse_args()


def split_csv_list(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def detect_format(path: Path, mode: str) -> str:
    if mode != "auto":
        return mode
    ext = path.suffix.lower()
    if ext == ".csv":
        return "csv"
    if ext == ".json":
        return "json"
    raise ValueError(f"Cannot infer format from extension: {path}")


def load_rows(path: Path, fmt: str) -> list[dict[str, Any]]:
    if fmt == "csv":
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON input must be a list of objects.")
    out: list[dict[str, Any]] = []
    for row in data:
        if isinstance(row, dict):
            out.append(row)
    return out


def parse_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_time_value(label: str, fallback_index: int) -> float:
    s = label.strip()
    # Common pattern: t0, t1, t12.5
    if s.lower().startswith("t"):
        num = parse_float(s[1:])
        if num is not None:
            return num
    # Direct numeric labels.
    num = parse_float(s)
    if num is not None:
        return num
    return float(fallback_index)


def companion_value(row: dict[str, Any], tcol: str, kind: str) -> Any:
    # accepted patterns:
    # lower_t0 / upper_t0
    # t0_lower / t0_upper
    # t0_lo / t0_hi
    keys = []
    if kind == "lower":
        keys = [f"lower_{tcol}", f"{tcol}_lower", f"{tcol}_lo"]
    elif kind == "upper":
        keys = [f"upper_{tcol}", f"{tcol}_upper", f"{tcol}_hi"]
    elif kind == "event":
        keys = [f"event_{tcol}", f"{tcol}_event"]
    for k in keys:
        if k in row:
            return row.get(k)
    return None


def infer_time_columns(
    rows: list[dict[str, Any]],
    panel_col: str,
    cohort_col: str,
    time_columns: list[str],
    exclude: set[str],
    time_regex: str,
) -> list[str]:
    if time_columns:
        return time_columns
    if not rows:
        return []
    pattern = re.compile(time_regex)
    cols = set()
    for r in rows:
        cols.update(r.keys())
    ignored = {
        panel_col,
        cohort_col,
        "panel",
        "cohort",
        "event",
        "lower",
        "upper",
        "time",
        "value",
    } | exclude
    out = []
    for c in sorted(cols):
        if c in ignored:
            continue
        if c.startswith("lower_") or c.startswith("upper_") or c.startswith("event_"):
            continue
        if c.endswith("_lower") or c.endswith("_upper") or c.endswith("_lo") or c.endswith("_hi") or c.endswith("_event"):
            continue
        if pattern.match(c):
            out.append(c)
    return out


def infer_grouped_columns(
    rows: list[dict[str, Any]],
    cohort_col: str,
    exclude: set[str],
    panel_time_regex: str,
) -> dict[str, list[str]]:
    if not rows:
        return {}
    pattern = re.compile(panel_time_regex)
    cols = set()
    for r in rows:
        cols.update(r.keys())
    ignored = {
        cohort_col,
        "cohort",
        "panel",
        "event",
        "lower",
        "upper",
        "time",
        "value",
    } | exclude
    grouped: dict[str, set[str]] = {}
    for c in cols:
        if c in ignored:
            continue
        m = pattern.match(c)
        if not m:
            continue
        panel = m.groupdict().get("panel")
        tname = m.groupdict().get("time")
        if not panel or not tname:
            continue
        if panel.endswith(("_lower", "_upper", "_event")):
            continue
        grouped.setdefault(panel, set()).add(tname)
    return {p: sorted(ts, key=lambda t: parse_time_value(t, 0)) for p, ts in sorted(grouped.items())}


def convert_wide_to_long(
    rows: list[dict[str, Any]],
    panel_col: str,
    cohort_col: str,
    default_panel: str,
    default_cohort: str,
    time_cols: list[str],
) -> list[dict[str, Any]]:
    long_rows: list[dict[str, Any]] = []
    ordered = sorted(time_cols, key=lambda c: parse_time_value(c, 0))
    for row in rows:
        panel = str(row.get(panel_col, row.get("panel", default_panel)))
        cohort = str(row.get(cohort_col, row.get("cohort", default_cohort)))
        for i, tcol in enumerate(ordered):
            value = parse_float(row.get(tcol))
            if value is None:
                continue
            t = parse_time_value(tcol, i)
            lower_raw = companion_value(row, tcol, "lower")
            upper_raw = companion_value(row, tcol, "upper")
            event_raw = companion_value(row, tcol, "event")
            lower = parse_float(lower_raw)
            upper = parse_float(upper_raw)
            long_rows.append(
                {
                    "panel": panel,
                    "cohort": cohort,
                    "time": t,
                    "value": value,
                    "lower": value if lower is None else lower,
                    "upper": value if upper is None else upper,
                    "event": "" if event_raw is None else str(event_raw),
                }
            )
    return long_rows


def grouped_companion_value(
    row: dict[str, Any], panel: str, tname: str, kind: str
) -> Any:
    # accepted patterns for grouped mode:
    # panel_lower_t0 / panel_upper_t0 / panel_event_t0
    # panel_t0_lower / panel_t0_upper / panel_t0_event
    # lower_panel_t0 / upper_panel_t0 / event_panel_t0
    keys = [
        f"{panel}_{kind}_{tname}",
        f"{panel}_{tname}_{kind}",
        f"{kind}_{panel}_{tname}",
    ]
    for k in keys:
        if k in row:
            return row.get(k)
    return None


def convert_grouped_to_long(
    rows: list[dict[str, Any]],
    cohort_col: str,
    default_cohort: str,
    grouped: dict[str, list[str]],
) -> list[dict[str, Any]]:
    long_rows: list[dict[str, Any]] = []
    for row in rows:
        cohort = str(row.get(cohort_col, row.get("cohort", default_cohort)))
        for panel, times in grouped.items():
            for i, tname in enumerate(times):
                val_key = f"{panel}_{tname}"
                value = parse_float(row.get(val_key))
                if value is None:
                    continue
                t = parse_time_value(tname, i)
                lower_raw = grouped_companion_value(row, panel, tname, "lower")
                upper_raw = grouped_companion_value(row, panel, tname, "upper")
                event_raw = grouped_companion_value(row, panel, tname, "event")
                lower = parse_float(lower_raw)
                upper = parse_float(upper_raw)
                long_rows.append(
                    {
                        "panel": panel,
                        "cohort": cohort,
                        "time": t,
                        "value": value,
                        "lower": value if lower is None else lower,
                        "upper": value if upper is None else upper,
                        "event": "" if event_raw is None else str(event_raw),
                    }
                )
    return long_rows


def save_rows(path: Path, fmt: str, rows: list[dict[str, Any]]) -> None:
    if fmt == "json":
        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        return
    fieldnames = ["panel", "cohort", "time", "value", "lower", "upper", "event"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)
    in_fmt = detect_format(in_path, args.input_format)
    out_fmt = detect_format(out_path, args.output_format)
    rows = load_rows(in_path, in_fmt)

    exclude = set(split_csv_list(args.exclude_columns))
    mode_note = ""
    if args.wide_mode == "row":
        explicit = split_csv_list(args.time_columns)
        inferred = infer_time_columns(
            rows=rows,
            panel_col=args.panel_col,
            cohort_col=args.cohort_col,
            time_columns=explicit,
            exclude=exclude,
            time_regex=args.time_regex,
        )
        if not inferred:
            msg = "No time columns inferred."
            if args.strict:
                raise ValueError(msg)
            print(f"⚠️  {msg} Output will be empty.")
        long_rows = convert_wide_to_long(
            rows=rows,
            panel_col=args.panel_col,
            cohort_col=args.cohort_col,
            default_panel=args.default_panel,
            default_cohort=args.default_cohort,
            time_cols=inferred,
        )
        if inferred:
            mode_note = f"time columns: {', '.join(inferred)}"
    else:
        grouped = infer_grouped_columns(
            rows=rows,
            cohort_col=args.cohort_col,
            exclude=exclude,
            panel_time_regex=args.panel_time_regex,
        )
        if not grouped:
            msg = "No grouped panel/time columns inferred."
            if args.strict:
                raise ValueError(msg)
            print(f"⚠️  {msg} Output will be empty.")
        long_rows = convert_grouped_to_long(
            rows=rows,
            cohort_col=args.cohort_col,
            default_cohort=args.default_cohort,
            grouped=grouped,
        )
        if grouped:
            mode_note = "panel groups: " + ", ".join(
                f"{p}[{len(ts)}]" for p, ts in grouped.items()
            )

    save_rows(out_path, out_fmt, long_rows)
    print(f"✅ Converted {len(rows)} wide rows -> {len(long_rows)} long rows")
    print(f"   input={in_path} ({in_fmt})")
    print(f"   output={out_path} ({out_fmt})")
    print(f"   wide_mode={args.wide_mode}")
    if mode_note:
        print(f"   {mode_note}")


if __name__ == "__main__":
    main()
