from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_design_patterns_gallery_layout_toggle_changes_output(tmp_path: Path) -> None:
    script = Path("examples-other/static/core/design_patterns_gallery.py")

    out_a = tmp_path / "gallery_a"
    out_b = tmp_path / "gallery_b"

    cmd_a = [
        sys.executable,
        str(script),
        "--recipes",
        "network",
        "--seed",
        "71",
        "--width",
        "1280",
        "--height",
        "720",
        "--output-prefix",
        str(out_a),
    ]
    cmd_b = [
        sys.executable,
        str(script),
        "--recipes",
        "network",
        "--seed",
        "71",
        "--width",
        "980",
        "--height",
        "720",
        "--output-prefix",
        str(out_b),
    ]

    subprocess.run(cmd_a, check=True, capture_output=True, text=True)
    subprocess.run(cmd_b, check=True, capture_output=True, text=True)

    svg_a = Path(f"{out_a}_network.svg")
    svg_b = Path(f"{out_b}_network.svg")
    assert _sha256(svg_a) != _sha256(svg_b)


def test_dataset_storyboard_topn_toggle_changes_scene_c_output(tmp_path: Path) -> None:
    script = Path("examples-other/data/storyboard/dataset_storyboard.py")

    out_a = tmp_path / "story_a"
    out_b = tmp_path / "story_b"

    base = [
        sys.executable,
        str(script),
        "--mode",
        "synthetic",
        "--seed",
        "131",
        "--groups",
        "4",
        "--categories",
        "5",
        "--points",
        "18",
        "--width",
        "1360",
        "--height",
        "840",
    ]
    cmd_a = [*base, "--scene-c-topn", "3", "--output-prefix", str(out_a)]
    cmd_b = [*base, "--scene-c-topn", "8", "--output-prefix", str(out_b)]

    subprocess.run(cmd_a, check=True, capture_output=True, text=True)
    subprocess.run(cmd_b, check=True, capture_output=True, text=True)

    scene_c_a = Path(f"{out_a}_scene_c_callouts.svg")
    scene_c_b = Path(f"{out_b}_scene_c_callouts.svg")
    assert _sha256(scene_c_a) != _sha256(scene_c_b)
