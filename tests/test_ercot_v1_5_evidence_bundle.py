"""Recompute every derived v1.5 figure from the published aggregate bundle."""

from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "recompute_ercot_v1_5_evidence.py"


def _load():
    spec = importlib.util.spec_from_file_location("recompute_ercot_v1_5_evidence", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_recomputes_evidence_and_checks_hashes() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "hashes match" in completed.stdout


def test_published_metrics_are_unchanged_and_promotion_is_not_a_pass() -> None:
    module = _load()
    measurements = json.loads((ROOT / "evidence" / "ercot_v1_5" / "measurements.json").read_text())
    evidence = json.loads((ROOT / "evidence" / "ercot_v1_5_validation.json").read_text())

    assert evidence["quantile_metrics"] == measurements["quantile_metrics"]
    assert evidence["calibration"] == measurements["calibration"]
    assert evidence["q50_mae_mw"] == measurements["q50_mae_mw"]
    assert evidence["quantile_crossings"] == measurements["quantile_crossings"]
    assert evidence["gates"][: len(measurements["published_numeric_gates"])] == measurements["published_numeric_gates"]
    assert evidence["decision"] == "evidence only, not packaged, endpoints stay gated"
    assert evidence["validation_status"] == "evidence_only_not_packaged"
    assert evidence["all_gates_passed"] is False
    assert evidence["packaging_authorized"] is False
    by_name = {gate["gate"]: gate for gate in evidence["gates"]}
    assert by_name["Evidence bundle"]["passed"] is False
    assert by_name["Feature availability"]["passed"] is False
    assert all(gate["passed"] for gate in measurements["published_numeric_gates"])


def test_exceedances_skill_and_q99_power_match_the_published_aggregates() -> None:
    module = _load()
    evidence = json.loads((ROOT / "evidence" / "ercot_v1_5_validation.json").read_text())
    derived = evidence["recomputed_from_published_aggregates"]["quantiles"]

    assert derived["q95"]["exceedances_inferred"] == 29
    assert derived["q99"]["exceedances_inferred"] == 8
    assert module.minimum_q99_exceedances_that_fail(672) == 27
    assert module.q99_gate_fails(672, 26) is False
    assert module.q99_gate_fails(672, 27) is True
    power = evidence["recomputed_from_published_aggregates"]["q99_probability_of_fail_given_true_coverage_0_96"]
    assert f"{power:.4f}" == "0.5178"
    assert f"{module.q99_fail_probability(672, 0.95):.4f}" == "0.8989"

    metrics = {row["quantile"]: row for row in evidence["quantile_metrics"]}
    for key, row in metrics.items():
        skill = 1.0 - row["pinball_loss"] / row["baseline_pinball_loss"]
        assert abs(skill - row["pinball_skill_vs_baseline"]) < 5.1e-7
        assert abs(abs(row["empirical_coverage"] - row["target_coverage"]) - row["absolute_coverage_error"]) < 5.1e-7
        assert derived[key]["point_estimate_calibration_gate_passed"] is True


def test_cross_window_illustration_is_labeled_and_uses_v1_4_identity() -> None:
    evidence = json.loads((ROOT / "evidence" / "ercot_v1_5_validation.json").read_text())
    v14 = json.loads((ROOT / "evidence" / "ercot_v1_4_validation.json").read_text())
    block = evidence["recomputed_from_published_aggregates"]
    implied = block["v1_4_q50_implied_baseline_on_v1_4_window"]
    q50_skill = next(row["pinball_skill_vs_baseline"] for row in v14["quantile_metrics"] if row["quantile"] == "q50")
    assert implied["implied_baseline_pinball"] == pytest_baseline(v14["q50_mae_mw"], q50_skill)
    illustration = block["cross_window_q50_skill_illustration"]
    q50_pinball = next(row["pinball_loss"] for row in evidence["quantile_metrics"] if row["quantile"] == "q50")
    assert illustration["value"] == 1.0 - q50_pinball / implied["implied_baseline_pinball"]
    assert "not a measured" in illustration["meaning"]
    assert f"{illustration['value']:.3f}" == "0.874"


def pytest_baseline(mae: float, skill: float) -> float:
    return (mae / 2.0) / (1.0 - skill)


def test_binomial_helper_matches_a_small_exact_probability() -> None:
    module = _load()
    # P(Binomial(5, 0.5) >= 4) = 6/32.
    assert math.isclose(module.binomial_probability(5, 0.5, lambda k: k >= 4), 6 / 32)


def test_hourly_rows_recompute_pinball_coverage_and_crossings() -> None:
    module = _load()
    rows = [
        {
            "actual_load_mw": 0.0,
            "pred_q50": 0.0,
            "pred_q90": 1.0,
            "pred_q95": 2.0,
            "pred_q99": 3.0,
            "baseline_q50": 0.0,
            "baseline_q90": 1.0,
            "baseline_q95": 2.0,
            "baseline_q99": 3.0,
        },
        {
            "actual_load_mw": 10.0,
            "pred_q50": 0.0,
            "pred_q90": 5.0,
            "pred_q95": 1.0,
            "pred_q99": 2.0,
            "baseline_q50": 0.0,
            "baseline_q90": 5.0,
            "baseline_q95": 1.0,
            "baseline_q99": 2.0,
        },
    ]

    result = module.metrics_from_evaluation_rows(rows)

    assert result["observations"] == 2
    assert result["q50"]["empirical_coverage"] == 0.5
    assert result["q50"]["pinball_loss"] == 2.5
    assert result["q50"]["pinball_skill_vs_baseline"] == 0.0
    assert result["q99"]["exceedances"] == 1
    assert result["quantile_crossings"] == 1
    assert result["finite_predictions"] is True
    assert result["q50_mae_mw"] == 5.0


def test_manifest_lists_the_missing_row_archive() -> None:
    manifest = json.loads((ROOT / "evidence" / "ercot_v1_5" / "manifest.json").read_text())

    assert manifest["row_level_archive_present"] is False
    missing = {item["path"] for item in manifest["missing_inputs"]}
    assert "evidence/ercot_v1_5/evaluation_rows.csv" in missing
    assert "evidence/ercot_v1_5/calibration_rows.csv" in missing
    assert not (ROOT / "evidence" / "ercot_v1_5" / "evaluation_rows.csv").exists()


def test_v1_4_rejection_is_unchanged() -> None:
    evidence = json.loads((ROOT / "evidence" / "ercot_v1_4_validation.json").read_text())
    record = (ROOT / "docs" / "DECISION_RECORD_ERCOT_v1_4.md").read_text(encoding="utf-8")

    assert evidence["validation_status"] == "rejected_candidate"
    assert evidence["all_gates_passed"] is False
    failed = {gate["gate"] for gate in evidence["gates"] if not gate["passed"]}
    assert failed == {"Q90 calibration error", "Q95 calibration error", "Q99 calibration error"}
    assert "Rejected for production" in record
    assert "Three of four calibration gates failed" in record


def test_decision_record_and_draft_state_the_required_limits() -> None:
    record = " ".join((ROOT / "docs" / "DECISION_RECORD_ERCOT_v1_5.md").read_text(encoding="utf-8").split())
    draft = " ".join((ROOT / "docs" / "PREREGISTRATION_ERCOT_FORECAST_WEATHER_DRAFT.md").read_text(encoding="utf-8").split())
    prereg = " ".join((ROOT / "docs" / "PREREGISTRATION_ERCOT_v1_5.md").read_text(encoding="utf-8").split())

    assert record.startswith("# Decision Record — ERCOT v1.5 probabilistic candidate: evidence only, not packaged")
    assert "evidence only, not packaged, endpoints stay gated" in record
    assert "2fcf2c9b528c1e309fc9912687466ad69d7899c2" in record
    assert "retrospective" in record.lower()
    assert "realized ERA5" in record
    assert "29" in record and "8" in record
    assert "0.5178" in record
    assert "2312.438609" in record
    assert "1276.07" in record
    assert "0.8739" in record
    assert "not a skill measured on the 672-hour window" in record
    assert "remains rejected" in record
    assert "Passes all preregistered gates" not in record

    assert "DRAFT - awaiting owner approval" in draft
    assert "Do not execute" in draft
    assert "×1.00" in draft
    assert "≤ 0.03" in draft
    assert "never imputed" in draft
    assert "Open-Meteo" in draft
    assert "2026-12-07" in draft
    assert "0.5178" in draft
    assert "has not been run" in draft or "does not run the evaluation" in draft

    assert "retrospective freeze" in prereg
    assert "2fcf2c9b528c1e309fc9912687466ad69d7899c2" in prereg
