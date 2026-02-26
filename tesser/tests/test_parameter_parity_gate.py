from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tesserax.parity import load_parity_manifest, validate_parity_manifest


def test_parameter_parity_manifest_passes_gate() -> None:
    payload = load_parity_manifest("examples-other/parameter_parity_manifest.json")
    issues = validate_parity_manifest(payload)
    assert issues == []


def test_parameter_parity_gate_logs_explicit_failure_reasons(tmp_path: Path) -> None:
    bad_manifest = {
        "examples": [
            {
                "example": "examples-other/animation/physics/animation_physics_overlay.py",
                "required_high_impact": ["--output", "--seed"],
                "rows": [
                    {
                        "legacy_param": "--output",
                        "new_api": "",
                        "status": "deprecated",
                    }
                ],
            }
        ]
    }
    manifest = tmp_path / "bad_manifest.json"
    manifest.write_text(json.dumps(bad_manifest, indent=2), encoding="utf-8")

    cmd = [
        sys.executable,
        "examples-other/validate_parameter_parity.py",
        "--manifest",
        str(manifest),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    assert proc.returncode == 2
    out = proc.stdout
    assert "PARITY_GATE: FAIL" in out
    assert "issue_count=" in out
    assert "reason=[E008]" in out
    assert "reason=[E011]" in out
    assert "reason=[E010]" in out
