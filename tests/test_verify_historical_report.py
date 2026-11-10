"""Diagnostics for the Historical Lab report checker.

The checker used to stop at the first bare mismatch ("rows[37]: numeric
mismatch"), which told a reviewer nothing about what was expected, what was
submitted, or why the two might differ. These tests pin the diagnostic
behavior: every mismatch is collected with its expected and submitted
values, and recognizable causes (shifted rows, rounding) are named.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

from scripts.verify_historical_report import (
    calculate,
    compare_all,
    diagnose,
    looks_like_rounding,
    rows_shift_amount,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = json.loads((ROOT / "public/data/historical-cases.json").read_text())
CASE = next(case for case in BUNDLE["cases"] if case["id"] == "summer-2023")


def build_report():
    rows, metrics = calculate(CASE, 80000, 5)
    report = {
        "schema": "gert-historical-report-v1",
        "analysis_version": "historical-capacity-v1",
        "dataset_version": BUNDLE["version"],
        "case_id": CASE["id"],
        "source_archive_sha256": CASE["source_archive_sha256"],
        "source_url": CASE["source_url"],
        "assumptions": {"capacity_mw": 80000,
                        "uniform_load_reduction_percent": 5,
                        "interval_hours": 1},
        "rows": copy.deepcopy(rows),
        "metrics": copy.deepcopy(metrics),
    }
    return report, rows, metrics


def run_cli(report, tmp_path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    return subprocess.run(
        [sys.executable, "scripts/verify_historical_report.py", "--report", str(path)],
        cwd=ROOT, capture_output=True, text=True,
    )


def test_correct_report_still_verifies(tmp_path):
    report, _, _ = build_report()
    result = run_cli(report, tmp_path)
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "report_verified"
    assert result.stderr == ""


def test_wrong_metric_lists_field_with_expected_and_actual():
    report, _, metrics = build_report()
    report["metrics"]["adjustedGapMwh"] += 250

    mismatches = compare_all(metrics, report["metrics"], "metrics")

    assert len(mismatches) == 1
    (mismatch,) = mismatches
    assert mismatch["path"] == "metrics.adjustedGapMwh"
    assert mismatch["expected"] == metrics["adjustedGapMwh"]
    assert mismatch["actual"] == metrics["adjustedGapMwh"] + 250
    assert mismatch["difference"] == 250


def test_compare_all_collects_every_mismatch():
    report, rows, metrics = build_report()
    report["metrics"]["recordedPeakMw"] += 1
    report["rows"][3]["originalGapMw"] += 10

    mismatches = compare_all(metrics, report["metrics"], "metrics")
    mismatches += compare_all(rows, report["rows"], "rows")

    assert {m["path"] for m in mismatches} == {
        "metrics.recordedPeakMw", "rows[3].originalGapMw"}


def test_shifted_rows_trigger_the_shift_note():
    report, rows, _ = build_report()
    # Each row displaced one position later: the classic off-by-one hour.
    report["rows"] = [report["rows"][-1]] + report["rows"][:-1]

    assert rows_shift_amount(rows, report["rows"]) == 1

    mismatches = compare_all(rows, report["rows"], "rows")
    text = diagnose(report, rows, mismatches)
    assert "shifted one hour later" in text
    assert "interval starts in America/Chicago" in text


def test_rounding_only_difference_is_classified_as_rounding():
    report, rows, metrics = build_report()
    report["metrics"]["adjustedGapMwh"] += 0.004

    mismatches = compare_all(metrics, report["metrics"], "metrics")

    assert len(mismatches) == 1
    assert looks_like_rounding(mismatches[0])
    assert "rounding" in diagnose(report, rows, mismatches)


def test_cli_prints_diagnostics_and_exits_1(tmp_path):
    report, _, metrics = build_report()
    report["metrics"]["adjustedGapMwh"] += 250

    result = run_cli(report, tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert "metrics.adjustedGapMwh" in result.stderr
    assert f"expected {metrics['adjustedGapMwh']!r}" in result.stderr
    assert f"report has {metrics['adjustedGapMwh'] + 250!r}" in result.stderr
    assert "capacity 80000 MW" in result.stderr
