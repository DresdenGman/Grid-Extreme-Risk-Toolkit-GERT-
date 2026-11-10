"""Recompute the v1.5 evidence document from the published aggregate bundle.

The row-level evaluation and calibration archives were not published. This
script therefore recomputes every derived number (coverage error, pinball
skill, Wilson intervals, exceedance counts, the Q99 gate power) from the
published aggregates and checks SHA-256 hashes. It does not invent the
missing rows, and it does not mark the evidence-bundle or feature-availability
gates as passed.

Check (default):

    python scripts/recompute_ercot_v1_5_evidence.py

Regenerate the evidence document and manifest after an intentional edit:

    python scripts/recompute_ercot_v1_5_evidence.py --write
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEASUREMENTS_PATH = ROOT / "evidence" / "ercot_v1_5" / "measurements.json"
EVIDENCE_PATH = ROOT / "evidence" / "ercot_v1_5_validation.json"
V14_EVIDENCE_PATH = ROOT / "evidence" / "ercot_v1_4_validation.json"
MANIFEST_PATH = ROOT / "evidence" / "ercot_v1_5" / "manifest.json"
SCRIPT_PATH = Path(__file__).resolve()

QUANTILES = ("q50", "q90", "q95", "q99")
TARGET = {"q50": Fraction(1, 2), "q90": Fraction(9, 10), "q95": Fraction(19, 20), "q99": Fraction(99, 100)}
COVERAGE_TOLERANCE = Fraction(3, 100)
WILSON_Z = 1.959963984540054  # standard normal 97.5th percentile
ISSUED_FORECAST_WEATHER = "issued_forecast_available_at_prediction_origin"
HASHED_PATHS = (
    "evidence/ercot_v1_5/measurements.json",
    "evidence/ercot_v1_5_validation.json",
    "evidence/ercot_v1_4_validation.json",
    "scripts/recompute_ercot_v1_5_evidence.py",
)
MISSING_ROW_INPUTS = (
    {
        "path": "evidence/ercot_v1_5/evaluation_rows.csv",
        "why": (
            "Hourly evaluation actuals, model quantiles, and baseline quantiles "
            "were not published, so pinball, coverage, MAE, crossings, and "
            "finiteness cannot be recomputed from rows."
        ),
    },
    {
        "path": "evidence/ercot_v1_5/calibration_rows.csv",
        "why": (
            "Hourly calibration actuals and center predictions were not published, "
            "so residual offsets and calibration-window coverage cannot be recomputed from rows."
        ),
    },
    {
        "path": "training_runs/ercot_v1/artifact/",
        "why": (
            "metadata.json, metrics.json, evaluation_report.json, backtest_sample.json, "
            "and model.joblib are gitignored and were not added to this bundle."
        ),
    },
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def log_binom_pmf(n: int, k: int, p: float) -> float:
    if not 0 <= p <= 1:
        raise ValueError("probability must be between 0 and 1")
    if p == 0.0:
        return 0.0 if k == 0 else math.inf * -1
    if p == 1.0:
        return 0.0 if k == n else math.inf * -1
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log(1.0 - p)
    )


def binomial_probability(n: int, p: float, keep) -> float:
    """Sum P(K=k) for k in 0..n where keep(k) is true. IID binomial only."""
    if n < 0:
        raise ValueError("n must be non-negative")
    logs = [log_binom_pmf(n, k, p) for k in range(n + 1) if keep(k)]
    if not logs:
        return 0.0
    finite = [item for item in logs if math.isfinite(item)]
    if not finite:
        return 0.0
    pivot = max(finite)
    return math.exp(pivot) * sum(math.exp(item - pivot) for item in finite)


def coverage_error(n: int, exceedances: int, target: Fraction) -> Fraction:
    return abs(Fraction(n - exceedances, n) - target)


def q99_gate_fails(n: int, exceedances: int) -> bool:
    """True when the absolute Q99 coverage error is strictly above 0.03."""
    return coverage_error(n, exceedances, TARGET["q99"]) > COVERAGE_TOLERANCE


def minimum_q99_exceedances_that_fail(n: int) -> int:
    for exceedances in range(n + 1):
        if q99_gate_fails(n, exceedances):
            return exceedances
    raise ValueError("no exceedance count fails the Q99 gate")


def q99_fail_probability(n: int, true_coverage: float) -> float:
    """P(Q99 absolute coverage error > 0.03 | IID true coverage)."""
    if not 0 <= true_coverage <= 1:
        raise ValueError("true coverage must be between 0 and 1")
    return binomial_probability(n, 1.0 - true_coverage, lambda k: q99_gate_fails(n, k))


def wilson_interval(successes: int, n: int, z: float = WILSON_Z) -> tuple[float, float]:
    phat = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (phat + z2 / (2.0 * n)) / denom
    half = z * math.sqrt(phat * (1.0 - phat) / n + z2 / (4.0 * n * n)) / denom
    return center - half, center + half


def inferred_covered_count(n: int, empirical_coverage: float) -> int:
    covered = int(round(n * empirical_coverage))
    if abs(covered / n - empirical_coverage) > 5.1e-7:
        raise ValueError(
            f"coverage {empirical_coverage} is not a unique six-decimal count at n={n}"
        )
    return covered


def pinball_loss(actual: list[float], predicted: list[float], alpha: float) -> float:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("pinball inputs must be non-empty and aligned")
    total = 0.0
    for y, yhat in zip(actual, predicted):
        gap = y - yhat
        total += alpha * gap if gap > 0 else (alpha - 1.0) * gap
    return total / len(actual)


def metrics_from_evaluation_rows(rows: list[dict[str, float]]) -> dict[str, object]:
    """Recompute evaluation-gate inputs from hourly rows.

    Required keys per row: actual_load_mw, pred_q50, pred_q90, pred_q95,
    pred_q99, baseline_q50, baseline_q90, baseline_q95, baseline_q99.
    """
    if not rows:
        raise ValueError("evaluation rows are empty")
    actual = [float(row["actual_load_mw"]) for row in rows]
    n = len(actual)
    result: dict[str, object] = {"observations": n}
    alphas = {"q50": 0.5, "q90": 0.9, "q95": 0.95, "q99": 0.99}
    predictions = {}
    for key, alpha in alphas.items():
        pred = [float(row[f"pred_{key}"]) for row in rows]
        baseline = [float(row[f"baseline_{key}"]) for row in rows]
        predictions[key] = pred
        model_pinball = pinball_loss(actual, pred, alpha)
        baseline_pinball = pinball_loss(actual, baseline, alpha)
        covered = sum(y <= yhat for y, yhat in zip(actual, pred))
        result[key] = {
            "empirical_coverage": covered / n,
            "pinball_loss": model_pinball,
            "baseline_pinball_loss": baseline_pinball,
            "pinball_skill_vs_baseline": 1.0 - model_pinball / baseline_pinball,
            "absolute_coverage_error": abs(covered / n - alpha),
            "covered_count": covered,
            "exceedances": n - covered,
        }
    crossings = 0
    finite = True
    for index in range(n):
        values = [predictions[key][index] for key in QUANTILES]
        finite = finite and all(math.isfinite(value) for value in values) and math.isfinite(actual[index])
        if any(left > right for left, right in zip(values, values[1:])):
            crossings += 1
    q50_mae = sum(abs(y - yhat) for y, yhat in zip(actual, predictions["q50"])) / n
    result["quantile_crossings"] = crossings
    result["quantile_crossing_rate"] = crossings / n
    result["finite_predictions"] = finite
    result["q50_mae_mw"] = q50_mae
    return result


def _quantile_map(rows: list[dict]) -> dict[str, dict]:
    mapped = {row["quantile"]: row for row in rows}
    if tuple(mapped) != QUANTILES and set(mapped) != set(QUANTILES):
        raise ValueError("quantile metrics must contain q50, q90, q95, and q99")
    return mapped


def _derived_quantile(row: dict, n: int) -> dict[str, object]:
    key = row["quantile"]
    covered = inferred_covered_count(n, row["empirical_coverage"])
    skill = 1.0 - row["pinball_loss"] / row["baseline_pinball_loss"]
    error = abs(row["empirical_coverage"] - row["target_coverage"])
    if abs(error - row["absolute_coverage_error"]) > 5.1e-7:
        raise ValueError(f"{key} absolute coverage error does not match the published coverage")
    if abs(skill - row["pinball_skill_vs_baseline"]) > 5.1e-7:
        raise ValueError(f"{key} pinball skill does not match the published pinball losses")
    low, high = wilson_interval(covered, n)
    published_low, published_high = row["coverage_wilson_95_ci"]
    if round(low, 4) != published_low or round(high, 4) != published_high:
        raise ValueError(f"{key} Wilson interval does not match the published rounded interval")
    return {
        "covered_count_inferred": covered,
        "exceedances_inferred": n - covered,
        "absolute_coverage_error": error,
        "pinball_skill_vs_baseline": skill,
        "wilson_95_ci": [low, high],
        "published_wilson_95_ci_matches_four_decimals": True,
        "point_estimate_calibration_gate_passed": error <= 0.03,
        "point_estimate_skill_gate_passed": skill > 0,
    }


def _v14_q50_implied_baseline(v14: dict) -> dict[str, float]:
    metrics = _quantile_map(v14["quantile_metrics"])
    q50 = metrics["q50"]
    # At q50, pinball loss is half of MAE. The v1.4 file publishes MAE and skill,
    # not the baseline pinball, so the baseline figure is implied by that identity.
    model_pinball = v14["q50_mae_mw"] / 2.0
    skill = q50["pinball_skill_vs_baseline"]
    if not 0 < skill < 1:
        raise ValueError("v1.4 q50 skill is outside the open unit interval")
    baseline = model_pinball / (1.0 - skill)
    return {
        "q50_mae_mw": v14["q50_mae_mw"],
        "q50_skill": skill,
        "implied_model_pinball": model_pinball,
        "implied_baseline_pinball": baseline,
    }


def build_evidence(measurements: dict, v14: dict) -> dict:
    n = measurements["observations"]
    if n != 672:
        raise ValueError("v1.5 published evaluation length is 672; refusing to silently change it")
    derived = {
        row["quantile"]: _derived_quantile(row, n) for row in measurements["quantile_metrics"]
    }
    skills = [item["pinball_skill_vs_baseline"] for item in derived.values()]
    if any(not item["point_estimate_skill_gate_passed"] for item in derived.values()):
        raise ValueError("published pinball skill is not positive")
    if measurements["quantile_crossing_rate"] > 0.05:
        raise ValueError("published crossing rate exceeds 0.05")
    v14_baseline = _v14_q50_implied_baseline(v14)
    q50_pinball = _quantile_map(measurements["quantile_metrics"])["q50"]["pinball_loss"]
    cross_window_skill = 1.0 - q50_pinball / v14_baseline["implied_baseline_pinball"]
    fail_at = minimum_q99_exceedances_that_fail(n)
    power_096 = q99_fail_probability(n, 0.96)
    power_095 = q99_fail_probability(n, 0.95)
    power_099 = q99_fail_probability(n, 0.99)
    feature_passed = measurements["evaluation_weather"] == ISSUED_FORECAST_WEATHER
    # Row files are not part of the published aggregate bundle. Their absence
    # is itself the evidence-bundle result: the gate stays failed.
    evidence_bundle_passed = False
    numeric_gates = json.loads(json.dumps(measurements["published_numeric_gates"]))
    gates = numeric_gates + [
        {
            "gate": "Evidence bundle",
            "observed": (
                "published aggregate summary only; hourly inputs and the model "
                "artifact were not archived"
            ),
            "passed": evidence_bundle_passed,
            "requirement": (
                "immutable metadata, evaluation, and backtest bundle sufficient "
                "to recompute every gate result from its inputs"
            ),
        },
        {
            "gate": "Feature availability",
            "observed": (
                "evaluation used realized ERA5 weather for the target hour; "
                "production requests an Open-Meteo forecast"
            ),
            "passed": feature_passed,
            "requirement": "serving features built only from information available at prediction time",
        },
    ]
    if any(gate["passed"] for gate in gates if gate["gate"] in {"Evidence bundle", "Feature availability"}):
        raise ValueError("refusing to mark the evidence-bundle or feature-availability gate passed")
    all_passed = all(gate["passed"] for gate in gates)
    return {
        "schema": "gert-ercot-v1.5-evidence-v2",
        "candidate_id": measurements["candidate_id"],
        "validation_status": "evidence_only_not_packaged",
        "decision": "evidence only, not packaged, endpoints stay gated",
        "packaging_authorized": False,
        "all_gates_passed": all_passed,
        "summary": (
            "Published 672-hour point estimates meet the numeric coverage, skill, "
            "crossing, and finiteness checks (maximum absolute coverage error "
            f"{max(row['absolute_coverage_error'] for row in measurements['quantile_metrics']):.6f}, "
            f"pinball skill {min(skills):.6f} to {max(skills):.6f}). "
            "The evidence-bundle and feature-availability gates are not passed. "
            "The candidate is evidence only: it is not packaged, and the "
            "prediction endpoints stay gated. The v1.4 rejection is unchanged."
        ),
        "published_at": measurements["published_at"],
        "preregistration": measurements["preregistration"],
        "preregistration_commit": "2fcf2c9b528c1e309fc9912687466ad69d7899c2",
        "source_results_commit": measurements["source_commit"],
        "training_window": measurements["training_window"],
        "calibration_window_start": measurements["calibration_window_start"],
        "calibration_window_end": measurements["calibration_window_end"],
        "evaluation_window_start": measurements["evaluation_window_start"],
        "evaluation_window_end": measurements["evaluation_window_end"],
        "observations": n,
        "calibration_observations": measurements["calibration_observations"],
        "q50_mae_mw": measurements["q50_mae_mw"],
        "quantile_crossings": measurements["quantile_crossings"],
        "quantile_crossing_rate": measurements["quantile_crossing_rate"],
        "calibration": measurements["calibration"],
        "quantile_metrics": measurements["quantile_metrics"],
        "gates": gates,
        "data_provenance": measurements["data_provenance"],
        "evaluation_weather": measurements["evaluation_weather"],
        "production_weather": measurements["production_weather"],
        "reproduction": measurements["reproduction"],
        "recomputed_from_published_aggregates": {
            "authority": (
                "Derived from the published aggregates in "
                "evidence/ercot_v1_5/measurements.json. Not recomputed from hourly rows."
            ),
            "quantiles": derived,
            "q99_exceedances_that_fail_the_gate": fail_at,
            "q99_probability_of_fail_given_true_coverage_0_96": power_096,
            "q99_probability_of_fail_given_true_coverage_0_95": power_095,
            "q99_probability_of_fail_given_true_coverage_0_99": power_099,
            "power_model": (
                "IID binomial. Hourly errors are dependent, so this is a sample-size "
                "illustration and not a grid-operations sample size. True coverage 0.96 "
                "sits on the 0.03 gate boundary, so this probability stays near one half "
                "as n grows."
            ),
            "v1_4_q50_implied_baseline_on_v1_4_window": v14_baseline,
            "cross_window_q50_skill_illustration": {
                "value": cross_window_skill,
                "meaning": (
                    "1 - (v1.5 q50 pinball / v1.4-window implied baseline pinball). "
                    "The two pinballs are from different hours. This is not a measured "
                    "skill on the 672-hour window."
                ),
            },
        },
        "not_recomputed_from_rows": [
            "empirical coverage",
            "pinball loss",
            "baseline pinball loss",
            "q50 MAE",
            "quantile crossings",
            "finiteness",
            "calibration residual offsets",
            "calibration-window coverage",
            "chosen multipliers",
        ],
        "limitations": [
            "Evaluation uses realized ERA5 weather for the target hour. Production weather is an Open-Meteo forecast. The published scores omit weather-forecast error and are an optimistic upper bound on forecast-weather performance. That train/serve skew fails feature availability and blocks packaging.",
            "The evidence bundle published with the result was an aggregate JSON. Hourly inputs, baseline predictions, and the model artifact were not archived, so the evidence-bundle gate is not passed. Derived identities below are checked; the primary measurements are transcribed.",
            "The preregistration commit 2fcf2c9b528c1e309fc9912687466ad69d7899c2 is dated 2026-11-05 03:11:19 PT, after the evaluation window closed. It is a retrospective freeze. Git does not show whether the series was inspected before that commit; the results commit is 2026-11-08.",
            "At n=672 the published coverages imply 29 Q95 exceedances and 8 Q99 exceedances. Under an IID binomial model, P(Q99 gate fails | true coverage 0.96) is about 0.52. The point-estimate gate is unchanged.",
            "The reported skill uses a seasonal baseline fit only on timestamps before 2025-01-01. v1.4's published q50 MAE and skill imply a baseline pinball near 1276 on the v1.4 window, versus 2312.438609 here. Those windows differ, so 0.93 and v1.4's 0.76-0.84 are not the same comparison.",
            "The v1.4 candidate remains rejected. No failed v1.4 gate is relabeled as a pass, and the 0.03 threshold is not moved.",
            "GERT is decision-support research and must not be used for autonomous grid control.",
        ],
    }


def build_manifest() -> dict:
    return {
        "schema": "gert-ercot-v1.5-evidence-manifest-v1",
        "files": [
            {"path": relative, "sha256": sha256_file(ROOT / relative)}
            for relative in HASHED_PATHS
        ],
        "missing_inputs": list(MISSING_ROW_INPUTS),
        "row_level_archive_present": False,
        "note": (
            "Hashes cover the published aggregates, the recomputed evidence document, "
            "the untouched v1.4 evidence file, and this script. The missing-input list "
            "is what a complete bundle would still need before the evidence-bundle gate "
            "could be reconsidered."
        ),
    }


def read_evaluation_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check() -> dict:
    measurements = load_json(MEASUREMENTS_PATH)
    v14 = load_json(V14_EVIDENCE_PATH)
    expected = build_evidence(measurements, v14)
    actual = load_json(EVIDENCE_PATH)
    if actual != expected:
        raise SystemExit("evidence/ercot_v1_5_validation.json does not match recomputation")
    manifest = load_json(MANIFEST_PATH)
    rebuilt = build_manifest()
    if manifest != rebuilt:
        raise SystemExit("evidence/ercot_v1_5/manifest.json does not match file hashes")
    if manifest["row_level_archive_present"] or expected["all_gates_passed"]:
        raise SystemExit("refusing a passed evidence bundle or a passed promotion")
    if v14["all_gates_passed"] or v14["validation_status"] != "rejected_candidate":
        raise SystemExit("v1.4 evidence no longer records a rejection")
    return expected


def write() -> None:
    measurements = load_json(MEASUREMENTS_PATH)
    v14 = load_json(V14_EVIDENCE_PATH)
    dump_json(EVIDENCE_PATH, build_evidence(measurements, v14))
    dump_json(MANIFEST_PATH, build_manifest())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate the evidence JSON and manifest")
    parser.add_argument("--power", type=float, help="print P(Q99 gate fails | this true coverage) at n=672")
    args = parser.parse_args()
    if args.power is not None:
        print(f"{q99_fail_probability(672, args.power):.10f}")
        return
    if args.write:
        write()
    check()
    print("v1.5 evidence recomputation and hashes match")


if __name__ == "__main__":
    main()
