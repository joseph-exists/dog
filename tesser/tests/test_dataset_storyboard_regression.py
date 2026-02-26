from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_dataset_storyboard_deterministic_regression(tmp_path: Path) -> None:
    script = Path("examples-other/data/storyboard/dataset_storyboard.py")
    out_prefix = tmp_path / "storyboard"
    report_dir = tmp_path / "reports"
    summary = report_dir / "summary.json"

    cmd = [
        sys.executable,
        str(script),
        "--mode",
        "synthetic",
        "--seed",
        "131",
        "--scene-b-panels",
        "4",
        "--scene-b-series",
        "3",
        "--scene-c-topn",
        "5",
        "--output-prefix",
        str(out_prefix),
        "--report-dir",
        str(report_dir),
        "--summary-report",
        str(summary),
    ]

    subprocess.run(cmd, check=True, capture_output=True, text=True)
    scene_a = Path(f"{out_prefix}_scene_a_profile.svg")
    scene_b = Path(f"{out_prefix}_scene_b_small_multiples.svg")
    scene_c = Path(f"{out_prefix}_scene_c_callouts.svg")
    h1 = (sha256_file(scene_a), sha256_file(scene_b), sha256_file(scene_c))

    subprocess.run(cmd, check=True, capture_output=True, text=True)
    h2 = (sha256_file(scene_a), sha256_file(scene_b), sha256_file(scene_c))

    assert h1 == h2

    # Validate summary hook payload shape and scene coverage.
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["mode"] == "synthetic"
    assert payload["seed"] == 131
    results = payload["results"]
    assert isinstance(results, list)
    assert len(results) == 3
    scenes = sorted(r.get("scene") for r in results)
    assert scenes == [
        "scene_a_profile",
        "scene_b_small_multiples",
        "scene_c_callouts",
    ]
    for row in results:
        assert "output_path" in row
        assert "config_fingerprint" in row
        assert "seed" in row

    # Validate per-scene report payload minimum schema.
    for name in (
        "scene_a_profile.json",
        "scene_b_small_multiples.json",
        "scene_c_callouts.json",
    ):
        report = json.loads((report_dir / name).read_text(encoding="utf-8"))
        assert report["format"] == "svg"
        assert "output_path" in report
        assert "metadata" in report
        assert "config_fingerprint" in report["metadata"]
