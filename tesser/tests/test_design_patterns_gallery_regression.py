from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_design_patterns_gallery_deterministic_regression(tmp_path: Path) -> None:
    script = Path("examples-other/static/core/design_patterns_gallery.py")
    out_prefix = tmp_path / "design_patterns_gallery"
    report_dir = tmp_path / "reports"
    summary = report_dir / "summary.json"

    cmd = [
        sys.executable,
        str(script),
        "--recipes",
        "all",
        "--seed",
        "71",
        "--width",
        "1280",
        "--height",
        "720",
        "--output-prefix",
        str(out_prefix),
        "--report-dir",
        str(report_dir),
        "--summary-report",
        str(summary),
    ]

    subprocess.run(cmd, check=True, capture_output=True, text=True)
    state_chart = Path(f"{out_prefix}_state_chart.svg")
    timeline = Path(f"{out_prefix}_timeline.svg")
    network = Path(f"{out_prefix}_network.svg")
    h1 = (sha256_file(state_chart), sha256_file(timeline), sha256_file(network))

    subprocess.run(cmd, check=True, capture_output=True, text=True)
    h2 = (sha256_file(state_chart), sha256_file(timeline), sha256_file(network))
    assert h1 == h2

    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["seed"] == 71
    assert payload["recipes"] == ["state_chart", "timeline", "network"]
    assert payload["parameter_schema_keys"] == [
        "export.format",
        "export.output_prefix",
        "export.report_dir",
        "export.summary_report",
        "layout.height",
        "layout.width",
        "motion.seed",
        "style.recipes",
    ]
    results = payload["results"]
    assert isinstance(results, list)
    assert len(results) == 3
    got_recipes = sorted(r.get("recipe", "") for r in results)
    assert got_recipes == ["network", "state_chart", "timeline"]
    for row in results:
        assert "output_path" in row
        assert "config_fingerprint" in row
        assert row.get("format") == "svg"

    for name in ("state_chart.json", "timeline.json", "network.json"):
        report = json.loads((report_dir / name).read_text(encoding="utf-8"))
        assert report["format"] == "svg"
        assert "output_path" in report
        assert "metadata" in report
        assert "config_fingerprint" in report["metadata"]
