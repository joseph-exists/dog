from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_gallery(tmp_path: Path, *extra: str) -> dict[str, object]:
    summary = tmp_path / "summary.json"
    cmd = [
        sys.executable,
        "examples-other/static/core/design_patterns_gallery.py",
        "--summary-report",
        str(summary),
        "--output-prefix",
        str(tmp_path / "gallery"),
        *extra,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(summary.read_text(encoding="utf-8"))


def test_gallery_quickstart_preset_resolves_expected_defaults(tmp_path: Path) -> None:
    payload = _run_gallery(tmp_path, "--preset", "quickstart")
    assert payload["preset"] == "quickstart"
    assert payload["recipes"] == ["state_chart", "timeline"]
    params = payload["resolved_params"]
    assert params["layout.width"] == 1100
    assert params["layout.height"] == 640
    assert params["motion.seed"] == 71


def test_gallery_expert_overrides_take_precedence_over_preset(tmp_path: Path) -> None:
    payload = _run_gallery(
        tmp_path,
        "--preset",
        "network_review",
        "--recipes",
        "state_chart",
        "--width",
        "1500",
        "--seed",
        "99",
    )
    assert payload["preset"] == "network_review"
    assert payload["recipes"] == ["state_chart"]
    params = payload["resolved_params"]
    assert params["layout.width"] == 1500
    assert params["motion.seed"] == 99
