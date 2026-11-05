"""Drift guard: the README's Evidence-at-a-glance tables must stay in sync
with the committed evidence bundle and the Historical Lab checker output.
If a future change regenerates the evidence or the dataset, this test fails
until the README tables are updated to match."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_gate_table_matches_evidence_json():
    evidence = json.loads((ROOT / "evidence" / "ercot_v1_4_validation.json").read_text())
    metrics = {m["quantile"]: m for m in evidence["quantile_metrics"]}

    for key in ("q50", "q90", "q95", "q99"):
        error = metrics[key]["absolute_coverage_error"]
        assert f"{error:.3f}" in README, f"README missing {key} coverage error {error:.3f}"

    skills = [m["pinball_skill_vs_baseline"] for m in evidence["quantile_metrics"]]
    assert f"+{min(skills):.2f} to +{max(skills):.2f}" in README
    assert evidence["quantile_crossings"] == 0


def _checker(case: str, capacity: int, reduction: int) -> dict:
    out = subprocess.run(
        [sys.executable, "scripts/verify_historical_report.py",
         "--case", case, "--capacity", str(capacity), "--reduction", str(reduction)],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)["metrics"]


def test_readme_historical_table_matches_checker():
    base = _checker("summer-2023", 80000, 0)
    reduced = _checker("summer-2023", 80000, 5)

    assert base["originalHoursAboveCapacity"] == 21
    assert f"{round(base['originalGapMwh']):,} MWh" in README
    assert reduced["adjustedHoursAboveCapacity"] == 7
    assert f"{round(reduced['adjustedGapMwh']):,} MWh" in README
    assert f"{base['minimumUniformReductionPercent']:.3f}%" in README
    assert f"{base['recordedPeakMw']:,.0f} MW" in README or f"{base['recordedPeakMw']:.0f} MW" in README
