"""Train and evaluate the first real ERCOT one-hour quantile model artifact."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_pinball_loss

from models.artifacts import load_model_artifact
from models.residual_quantile import ResidualQuantileBundle
from training.ercot.features import SERVED_FEATURE_COLUMNS


QUANTILES = (0.5, 0.9, 0.95, 0.99)
QUANTILE_KEYS = {0.5: "q50", 0.9: "q90", 0.95: "q95", 0.99: "q99"}
CALIBRATION_SHRINKAGE = {"q50": 0.40, "q90": 0.90, "q95": 0.90, "q99": 0.55}
CALIBRATION_MODES = ("fixed", "grid")
GRID_MULTIPLIER_MIN = 0.50
GRID_MULTIPLIER_MAX = 1.50
GRID_MULTIPLIER_STEP = 0.01
INPUT_PATH = Path("training_runs/ercot_v1/features.csv")
ARTIFACT_DIR = Path("training_runs/ercot_v1/artifact")


def split_periods(
    frame: pd.DataFrame, evaluation_year: int = 2025
) -> tuple[pd.DataFrame, pd.DataFrame]:
    timestamps = pd.to_datetime(frame["timestamp_utc"], utc=True)
    years = timestamps.dt.tz_convert("America/Chicago").dt.year
    training = frame.loc[years < evaluation_year].copy()
    evaluation = frame.loc[years == evaluation_year].copy()
    if training.empty or evaluation.empty:
        raise ValueError(
            f"Expected non-empty pre-{evaluation_year} training and {evaluation_year} evaluation periods"
        )
    return training, evaluation


def split_evaluation_window(
    frame: pd.DataFrame,
    evaluation_year: int,
    evaluation_start: str | None = None,
    evaluation_end: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return strictly earlier training data and a closed UTC evaluation window."""
    if evaluation_start is None and evaluation_end is None:
        return split_periods(frame, evaluation_year)
    if not evaluation_start or not evaluation_end:
        raise ValueError("evaluation_start and evaluation_end must be provided together")
    timestamps = pd.to_datetime(frame["timestamp_utc"], utc=True)
    start = pd.to_datetime(evaluation_start, utc=True)
    end = pd.to_datetime(evaluation_end, utc=True) + pd.Timedelta(days=1) - pd.Timedelta(hours=1)
    if start > end:
        raise ValueError("evaluation_start must not be after evaluation_end")
    training = frame.loc[timestamps < start].copy()
    evaluation = frame.loc[(timestamps >= start) & (timestamps <= end)].copy()
    if training.empty or evaluation.empty:
        raise ValueError("Expected non-empty training and evaluation windows")
    return training, evaluation


def fit_center_estimator(
    frame: pd.DataFrame, feature_names: list[str]
) -> HistGradientBoostingRegressor:
    estimator = HistGradientBoostingRegressor(
        loss="absolute_error",
        max_iter=300,
        max_depth=6,
        learning_rate=0.08,
        l2_regularization=1.0,
        random_state=42,
    )
    estimator.fit(
        frame[feature_names].to_numpy(dtype=float),
        (
            frame["actual_load_mw"].to_numpy(dtype=float)
            - frame["lag_load_1h"].to_numpy(dtype=float)
        ),
    )
    return estimator


def residual_offsets(
    development: pd.DataFrame,
    calibration: pd.DataFrame,
    feature_names: list[str],
) -> dict[str, float]:
    center = fit_center_estimator(development, feature_names)
    residuals = (
        calibration["actual_load_mw"].to_numpy(dtype=float)
        - calibration["lag_load_1h"].to_numpy(dtype=float)
        - center.predict(calibration[feature_names].to_numpy(dtype=float))
    )
    offsets = {
        QUANTILE_KEYS[quantile]: float(np.quantile(residuals, quantile))
        * CALIBRATION_SHRINKAGE[QUANTILE_KEYS[quantile]]
        for quantile in QUANTILES
    }
    ordered = np.sort(np.array([offsets[QUANTILE_KEYS[q]] for q in QUANTILES]))
    return {
        QUANTILE_KEYS[quantile]: float(ordered[index])
        for index, quantile in enumerate(QUANTILES)
    }


def split_calibration_evaluation_windows(
    frame: pd.DataFrame,
    training_end: str,
    calibration_start: str,
    calibration_end: str,
    evaluation_start: str,
    evaluation_end: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split a frame into training, calibration, and closed UTC evaluation windows.

    Training keeps timestamps strictly before ``training_end``; the calibration
    and evaluation windows are closed UTC ranges [start 00:00, end 23:00].
    """
    timestamps = pd.to_datetime(frame["timestamp_utc"], utc=True)
    training_limit = pd.to_datetime(training_end, utc=True)

    def closed_window(start: str, end: str) -> tuple[pd.Timestamp, pd.Timestamp]:
        window_start = pd.to_datetime(start, utc=True)
        window_end = pd.to_datetime(end, utc=True) + pd.Timedelta(days=1) - pd.Timedelta(hours=1)
        if window_start > window_end:
            raise ValueError("window start must not be after window end")
        return window_start, window_end

    calibration_first, calibration_last = closed_window(calibration_start, calibration_end)
    evaluation_first, evaluation_last = closed_window(evaluation_start, evaluation_end)
    if calibration_last >= evaluation_first:
        raise ValueError("calibration window must end before the evaluation window starts")
    training = frame.loc[timestamps < training_limit].copy()
    calibration = frame.loc[(timestamps >= calibration_first) & (timestamps <= calibration_last)].copy()
    evaluation = frame.loc[(timestamps >= evaluation_first) & (timestamps <= evaluation_last)].copy()
    if training.empty or calibration.empty or evaluation.empty:
        raise ValueError("Expected non-empty training, calibration, and evaluation windows")
    return training, calibration, evaluation


def grid_multipliers() -> list[float]:
    steps = int(round((GRID_MULTIPLIER_MAX - GRID_MULTIPLIER_MIN) / GRID_MULTIPLIER_STEP))
    return [round(GRID_MULTIPLIER_MIN + GRID_MULTIPLIER_STEP * step, 2) for step in range(steps + 1)]


def choose_multiplier(
    actual: np.ndarray,
    center_predictions: np.ndarray,
    base_offset: float,
    target_coverage: float,
) -> tuple[float, float]:
    """Pick the grid multiplier whose calibration coverage is closest to target.

    The grid is scanned in ascending order and a candidate only replaces the
    incumbent on a strict improvement, so ties resolve to the smaller
    multiplier, as preregistered.
    """
    best_multiplier: float | None = None
    best_coverage: float | None = None
    best_error: float | None = None
    for multiplier in grid_multipliers():
        coverage = float(np.mean(actual <= center_predictions + multiplier * base_offset))
        error = abs(coverage - target_coverage)
        if best_error is None or error < best_error - 1e-12:
            best_multiplier, best_coverage, best_error = multiplier, coverage, error
    if best_multiplier is None or best_coverage is None:
        raise ValueError("Multiplier grid search evaluated no candidates")
    return best_multiplier, best_coverage


def grid_calibrated_offsets(
    training: pd.DataFrame,
    calibration: pd.DataFrame,
    feature_names: list[str],
) -> tuple[dict[str, float], dict[str, object]]:
    """Recalibrate residual offsets per quantile on the calibration window only.

    Base offsets are the empirical residual quantiles on the calibration
    window (center fitted on the training data, exactly as in the fixed
    path); each offset is then scaled by the multiplier chosen by
    :func:`choose_multiplier`, and the scaled offsets are kept in
    non-decreasing order.
    """
    center = fit_center_estimator(training, feature_names)
    center_predictions = center.predict(
        calibration[feature_names].to_numpy(dtype=float)
    ) + calibration["lag_load_1h"].to_numpy(dtype=float)
    actual = calibration["actual_load_mw"].to_numpy(dtype=float)
    residuals = actual - center_predictions
    base_offsets = {
        QUANTILE_KEYS[quantile]: float(np.quantile(residuals, quantile)) for quantile in QUANTILES
    }
    multipliers: dict[str, float] = {}
    calibration_coverage: dict[str, float] = {}
    for quantile in QUANTILES:
        key = QUANTILE_KEYS[quantile]
        multiplier, coverage = choose_multiplier(actual, center_predictions, base_offsets[key], quantile)
        multipliers[key] = multiplier
        calibration_coverage[key] = coverage
    scaled = [base_offsets[QUANTILE_KEYS[q]] * multipliers[QUANTILE_KEYS[q]] for q in QUANTILES]
    ordered = np.sort(np.array(scaled))
    offsets = {QUANTILE_KEYS[quantile]: float(ordered[index]) for index, quantile in enumerate(QUANTILES)}
    details: dict[str, object] = {
        "mode": "grid",
        "grid": {
            "min": GRID_MULTIPLIER_MIN,
            "max": GRID_MULTIPLIER_MAX,
            "step": GRID_MULTIPLIER_STEP,
            "objective": "minimize |empirical coverage - target coverage| on the calibration window",
            "tie_break": "smaller multiplier",
        },
        "multipliers": multipliers,
        "base_residual_offsets_mw": base_offsets,
        "calibration_empirical_coverage": calibration_coverage,
    }
    return offsets, details


def monotonic_predictions(predictions: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], float]:
    matrix = np.column_stack([predictions[QUANTILE_KEYS[q]] for q in QUANTILES])
    crossing = np.any(np.diff(matrix, axis=1) < 0, axis=1)
    sorted_matrix = np.sort(matrix, axis=1)
    return (
        {QUANTILE_KEYS[q]: sorted_matrix[:, index] for index, q in enumerate(QUANTILES)},
        float(np.mean(crossing)),
    )


def local_years(frame: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(frame["timestamp_utc"], utc=True).dt.tz_convert("America/Chicago").dt.year


def fit_annual_trend(frame: pd.DataFrame) -> tuple[float, float, int, dict[int, float]]:
    years = local_years(frame)
    annual_means = frame.assign(_year=years).groupby("_year")["actual_load_mw"].mean()
    if len(annual_means) < 2:
        raise ValueError("At least two annual means are required for trend estimation")
    base_year = int(annual_means.index.min())
    slope, intercept = np.polyfit(
        annual_means.index.to_numpy(dtype=float) - base_year,
        np.log(annual_means.to_numpy(dtype=float)),
        1,
    )
    return (
        float(intercept),
        float(slope),
        base_year,
        {int(year): float(value) for year, value in annual_means.items()},
    )


def projected_scale(years: np.ndarray, intercept: float, slope: float, base_year: int) -> np.ndarray:
    return np.exp(intercept + slope * (years.astype(float) - float(base_year)))


def fit_normalized_estimators(
    frame: pd.DataFrame,
    core_features: list[str],
) -> tuple[dict[str, HistGradientBoostingRegressor], tuple[float, float, int]]:
    intercept, slope, base_year, annual_means = fit_annual_trend(frame)
    years = local_years(frame)
    normalized_target = frame["actual_load_mw"].to_numpy(dtype=float) / years.map(annual_means).to_numpy(dtype=float)
    X = frame[core_features].to_numpy(dtype=float)
    estimator = HistGradientBoostingRegressor(
        loss="absolute_error",
        max_iter=300,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
    )
    estimator.fit(X, normalized_target)
    # A shared center estimate plus ordered out-of-sample residual quantiles
    # prevents quantile crossing by construction.
    estimators = {key: estimator for key in QUANTILE_KEYS.values()}
    return estimators, (intercept, slope, base_year)


def predict_with_components(
    estimators: dict[str, HistGradientBoostingRegressor],
    trend: tuple[float, float, int],
    frame: pd.DataFrame,
    core_features: list[str],
    calibration_ratio: dict[str, float] | None = None,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    intercept, slope, base_year = trend
    scale = projected_scale(local_years(frame).to_numpy(), intercept, slope, base_year)
    X = frame[core_features].to_numpy(dtype=float)
    calibration = calibration_ratio or {}
    return (
        {
            key: estimator.predict(X) * scale + float(calibration.get(key, 0.0)) * scale
            for key, estimator in estimators.items()
        },
        scale,
    )


def seasonal_baseline(training: pd.DataFrame, evaluation: pd.DataFrame) -> dict[str, np.ndarray]:
    intercept, slope, base_year, annual_means = fit_annual_trend(training)
    normalized = training.copy()
    normalized["_ratio"] = (
        normalized["actual_load_mw"].to_numpy(dtype=float)
        / local_years(normalized).map(annual_means).to_numpy(dtype=float)
    )
    scale = projected_scale(local_years(evaluation).to_numpy(), intercept, slope, base_year)
    result: dict[str, np.ndarray] = {}
    for quantile in QUANTILES:
        grouped = normalized.groupby(["month", "hour"])["_ratio"].quantile(quantile)
        fallback = float(normalized["_ratio"].quantile(quantile))
        ratios = np.array(
            [float(grouped.get((row.month, row.hour), fallback)) for row in evaluation.itertuples()]
        )
        result[QUANTILE_KEYS[quantile]] = ratios * scale
    return result


def metric_bundle(y: np.ndarray, predictions: dict[str, np.ndarray]) -> dict[str, dict[str, float]]:
    pinball: dict[str, float] = {}
    coverage: dict[str, float] = {}
    for quantile in QUANTILES:
        key = QUANTILE_KEYS[quantile]
        pinball[key] = float(mean_pinball_loss(y, predictions[key], alpha=quantile))
        coverage[key] = float(np.mean(y <= predictions[key]))
    return {"pinball_loss": pinball, "empirical_coverage": coverage}


def train(
    features_path: Path,
    artifact_dir: Path,
    evaluation_year: int = 2025,
    model_version: str = "ercot-lag-residual-gbt-v1.3.0-candidate",
    evaluation_start: str | None = None,
    evaluation_end: str | None = None,
    calibration_mode: str = "fixed",
    calibration_start: str | None = None,
    calibration_end: str | None = None,
    training_end: str | None = None,
) -> dict[str, object]:
    if calibration_mode not in CALIBRATION_MODES:
        raise ValueError(f"calibration_mode must be one of {CALIBRATION_MODES}")
    frame = pd.read_csv(features_path)
    required = {"timestamp_utc", "actual_load_mw", *SERVED_FEATURE_COLUMNS}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Feature table missing columns: {sorted(missing)}")
    feature_names = list(SERVED_FEATURE_COLUMNS)
    calibration_details: dict[str, object]
    if calibration_mode == "grid":
        if not (training_end and calibration_start and calibration_end and evaluation_start and evaluation_end):
            raise ValueError(
                "grid calibration requires training_end, calibration_start, calibration_end, "
                "evaluation_start, and evaluation_end"
            )
        training, calibration, evaluation = split_calibration_evaluation_windows(
            frame,
            training_end,
            calibration_start,
            calibration_end,
            evaluation_start,
            evaluation_end,
        )
        offsets, calibration_details = grid_calibrated_offsets(training, calibration, feature_names)
    else:
        training, evaluation = split_evaluation_window(
            frame, evaluation_year, evaluation_start, evaluation_end
        )
        evaluation_first = pd.to_datetime(evaluation["timestamp_utc"], utc=True).min()
        internal_calibration_start = evaluation_first - pd.DateOffset(years=1)
        training_timestamps = pd.to_datetime(training["timestamp_utc"], utc=True)
        development = training.loc[training_timestamps < internal_calibration_start].copy()
        calibration = training.loc[training_timestamps >= internal_calibration_start].copy()
        if development.empty or calibration.empty:
            raise ValueError(
                "A recent calibration window and earlier development data are required"
            )
        offsets = residual_offsets(development, calibration, feature_names)
        calibration_details = {"mode": "fixed", "shrinkage": CALIBRATION_SHRINKAGE}
    y_eval = evaluation["actual_load_mw"].to_numpy(dtype=float)

    center_estimator = fit_center_estimator(training, feature_names)
    center_predictions = center_estimator.predict(
        evaluation[feature_names].to_numpy(dtype=float)
    ) + evaluation["lag_load_1h"].to_numpy(dtype=float)
    raw_predictions = {
        key: center_predictions + offset for key, offset in offsets.items()
    }
    bundle = ResidualQuantileBundle(
        center_estimator=center_estimator,
        residual_offsets_mw=offsets,
        anchor_feature_index=feature_names.index("lag_load_1h"),
    )
    predictions, crossing_rate = monotonic_predictions(raw_predictions)
    model_metrics = metric_bundle(y_eval, predictions)
    baseline_predictions = seasonal_baseline(training, evaluation)
    baseline_metrics = metric_bundle(y_eval, baseline_predictions)
    skill = {
        key: 1.0 - model_metrics["pinball_loss"][key] / baseline_metrics["pinball_loss"][key]
        for key in QUANTILE_KEYS.values()
    }
    coverage_error = {
        QUANTILE_KEYS[q]: abs(model_metrics["empirical_coverage"][QUANTILE_KEYS[q]] - q)
        for q in QUANTILES
    }
    gates = {
        "positive_pinball_skill_all_quantiles": all(value > 0 for value in skill.values()),
        "coverage_error_at_most_0_03_all_quantiles": all(value <= 0.03 for value in coverage_error.values()),
        "quantile_crossing_rate_at_most_0_05": crossing_rate <= 0.05,
        "finite_predictions": all(np.isfinite(value).all() for value in predictions.values()),
    }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, artifact_dir / "model.joblib")
    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    training_local_dates = pd.to_datetime(training["timestamp_utc"], utc=True).dt.tz_convert(
        "America/Chicago"
    ).dt.date
    evaluation_local_dates = pd.to_datetime(evaluation["timestamp_utc"], utc=True).dt.tz_convert(
        "America/Chicago"
    ).dt.date
    calibration_local_dates = pd.to_datetime(calibration["timestamp_utc"], utc=True).dt.tz_convert(
        "America/Chicago"
    ).dt.date
    metadata = {
        "artifact_schema_version": "1.3",
        "validation_status": (
            "provisional_candidate" if all(gates.values()) else "rejected_candidate"
        ),
        "model_name": "gert_ercot_system_quantile",
        "model_version": model_version,
        "model_type": "sklearn_quantile_bundle",
        "created_at": created_at,
        "training_period": {
            "start": min(training_local_dates).isoformat(),
            "end": max(training_local_dates).isoformat(),
        },
        "forecast_contract": {
            "forecast_origin": "request_time",
            "target_horizon_hours": 1,
            "target_variable": "grid_load_mw",
        },
        "feature_names": feature_names,
        "feature_units": {
            "temperature": "degC", "wind_speed": "m/s", "solar_irradiance": "W/m2",
            "hour": "local_hour", "day_of_week": "integer_0_monday",
            "month": "integer_1_january", "is_weekend": "binary",
            "year": "ercot_local_year",
            "lag_load_1h": "MW", "lag_load_24h": "MW", "lag_load_168h": "MW",
            "rolling_load_mean_24h": "MW", "rolling_load_std_24h": "MW",
            "rolling_load_mean_168h": "MW", "rolling_load_std_168h": "MW",
        },
        "quantiles": list(QUANTILES),
        "supported_regions": ["ERCOT_SYSTEM"],
        "training_data": {
            "source": "ERCOT NP6-346-CD + Open-Meteo ERA5",
            "provenance": (
                "Official ERCOT hourly system load joined to fixed-weight four-zone ERA5 weather; "
                f"{min(evaluation_local_dates).isoformat()} through "
                f"{max(evaluation_local_dates).isoformat()} held out"
            ),
        },
        "runtime": {
            "python_version": platform.python_version(),
            "scikit_learn_version": sklearn.__version__,
        },
        "calibration": {
            "form": "lag-1 anchored load increments plus ordered residual quantiles",
            "period_start": min(calibration_local_dates).isoformat(),
            "period_end": max(calibration_local_dates).isoformat(),
            "window_start_utc": pd.to_datetime(calibration["timestamp_utc"], utc=True).min().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "window_end_utc": pd.to_datetime(calibration["timestamp_utc"], utc=True).max().strftime("%Y-%m-%dT%H:%M:%SZ"),
            **calibration_details,
            "residual_offsets_mw": offsets,
        },
    }
    metrics = {
        "evaluation_period": {
            "start": min(evaluation_local_dates).isoformat(),
            "end": max(evaluation_local_dates).isoformat(),
        },
        "sample_count": int(len(evaluation)),
        **model_metrics,
        "wis": None,
        "quantile_crossing_rate": crossing_rate,
    }
    if calibration_mode == "grid":
        calibration_limitation = (
            "Calibration multipliers were selected on the preregistered calibration window only; "
            "the evaluation window was not inspected before calibration was frozen."
        )
    else:
        calibration_limitation = (
            "Calibration shrinkage was frozen on the development evaluation before the final blind holdout."
        )
    report = {
        "candidate_passed_all_gates": all(gates.values()),
        "gates": gates,
        "pinball_skill_vs_month_hour_climatology": skill,
        "coverage_absolute_error": coverage_error,
        "q50_mae_mw": float(mean_absolute_error(y_eval, predictions["q50"])),
        "baseline": baseline_metrics,
        "model": model_metrics,
        "calibration": calibration_details,
        "calibration_sample_count": int(len(calibration)),
        "known_limitations": [
            "Historical training uses ERA5 realized target-hour weather; production uses a one-hour weather forecast.",
            "Operational load features require 168 contiguous official ERCOT observations.",
            "The conditional center is anchored to the latest official load and predicts a one-hour increment.",
            "WIS is unavailable because the served artifact contains upper quantiles only.",
            calibration_limitation,
        ],
    }
    peak_index = int(np.argmax(y_eval))
    sample_start = max(0, min(len(evaluation) - 168, peak_index - 84))
    sample_end = min(len(evaluation), sample_start + 168)
    backtest_sample = [
        {
            "hour": offset,
            "timestamp_utc": str(evaluation.iloc[index]["timestamp_utc"]),
            "actual_load": float(y_eval[index]),
            "baseline_p99": float(baseline_predictions["q99"][index]),
            "gert_p99": float(predictions["q99"][index]),
        }
        for offset, index in enumerate(range(sample_start, sample_end))
    ]
    for name, document in (("metadata.json", metadata), ("metrics.json", metrics), ("evaluation_report.json", report)):
        (artifact_dir / name).write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (artifact_dir / "backtest_sample.json").write_text(
        json.dumps(backtest_sample, indent=2) + "\n", encoding="utf-8"
    )
    load_model_artifact(artifact_dir)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, default=INPUT_PATH)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    parser.add_argument("--evaluation-year", type=int, default=2025)
    parser.add_argument("--evaluation-start", help="Optional UTC evaluation start date (YYYY-MM-DD)")
    parser.add_argument("--evaluation-end", help="Optional UTC evaluation end date (YYYY-MM-DD)")
    parser.add_argument(
        "--model-version",
        default="ercot-lag-residual-gbt-v1.3.0-candidate",
    )
    parser.add_argument(
        "--calibration-mode",
        choices=CALIBRATION_MODES,
        default="fixed",
        help="fixed reproduces the v1.4 shrinkage path; grid runs the preregistered per-quantile recalibration",
    )
    parser.add_argument("--training-end", help="Grid mode: training keeps UTC timestamps before this date (YYYY-MM-DD)")
    parser.add_argument("--calibration-start", help="Grid mode: UTC calibration window start date (YYYY-MM-DD)")
    parser.add_argument("--calibration-end", help="Grid mode: UTC calibration window end date (YYYY-MM-DD)")
    args = parser.parse_args()
    report = train(
        args.features,
        args.artifact_dir,
        evaluation_year=args.evaluation_year,
        model_version=args.model_version,
        evaluation_start=args.evaluation_start,
        evaluation_end=args.evaluation_end,
        calibration_mode=args.calibration_mode,
        calibration_start=args.calibration_start,
        calibration_end=args.calibration_end,
        training_end=args.training_end,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
