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
from models.trend_quantile import TrendQuantileBundle
from training.ercot.features import SERVED_FEATURE_COLUMNS


QUANTILES = (0.5, 0.9, 0.95, 0.99)
QUANTILE_KEYS = {0.5: "q50", 0.9: "q90", 0.95: "q95", 0.99: "q99"}
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
    model_version: str = "ercot-trend-conformal-gbt-v1.2.0-candidate",
) -> dict[str, object]:
    frame = pd.read_csv(features_path)
    required = {"timestamp_utc", "actual_load_mw", *SERVED_FEATURE_COLUMNS}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Feature table missing columns: {sorted(missing)}")
    training, evaluation = split_periods(frame, evaluation_year)
    feature_names = list(SERVED_FEATURE_COLUMNS)
    core_features = [name for name in feature_names if name != "year"]
    y_eval = evaluation["actual_load_mw"].to_numpy(dtype=float)

    training_years = local_years(training)
    rolling_residual_ratios: list[np.ndarray] = []
    calibration_years = tuple(range(evaluation_year - 3, evaluation_year))
    for calibration_year in calibration_years:
        development = training.loc[training_years < calibration_year].copy()
        calibration = training.loc[training_years == calibration_year].copy()
        if development.empty or calibration.empty:
            raise ValueError(f"Missing rolling-origin data for calibration year {calibration_year}")
        calibration_estimators, calibration_trend = fit_normalized_estimators(development, core_features)
        calibration_predictions, calibration_scale = predict_with_components(
            calibration_estimators, calibration_trend, calibration, core_features
        )
        y_calibration = calibration["actual_load_mw"].to_numpy(dtype=float)
        rolling_residual_ratios.append(
            (y_calibration - calibration_predictions["q50"]) / calibration_scale
        )
    pooled_residual_ratio = np.concatenate(rolling_residual_ratios)
    calibration_ratio = {
        QUANTILE_KEYS[quantile]: float(np.quantile(pooled_residual_ratio, quantile))
        for quantile in QUANTILES
    }

    estimators, trend = fit_normalized_estimators(training, core_features)
    raw_predictions, _ = predict_with_components(
        estimators, trend, evaluation, core_features, calibration_ratio
    )
    intercept, slope, base_year = trend
    bundle = TrendQuantileBundle(
        estimators=estimators,
        trend_intercept=intercept,
        trend_slope=slope,
        trend_base_year=base_year,
        calibration_ratio=calibration_ratio,
        year_feature_index=feature_names.index("year"),
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
    metadata = {
        "artifact_schema_version": "1.2",
        "model_name": "gert_ercot_system_quantile",
        "model_version": model_version,
        "model_type": "sklearn_quantile_bundle",
        "created_at": created_at,
        "training_period": {
            "start": str(local_years(training).min()) + "-01-01",
            "end": str(evaluation_year - 1) + "-12-31",
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
        },
        "quantiles": list(QUANTILES),
        "supported_regions": ["ERCOT_SYSTEM"],
        "training_data": {
            "source": "ERCOT NP6-346-CD + Open-Meteo ERA5",
            "provenance": (
                "Official ERCOT hourly system load joined to fixed-weight four-zone ERA5 weather; "
                f"{evaluation_year} held out"
            ),
        },
        "runtime": {
            "python_version": platform.python_version(),
            "scikit_learn_version": sklearn.__version__,
        },
        "trend": {
            "form": "log_linear_annual_mean",
            "base_year": base_year,
            "annual_growth_rate": float(np.exp(slope) - 1.0),
            "calibration_period": "rolling-origin " + "/".join(str(year) for year in calibration_years),
        },
    }
    evaluation_local_dates = pd.to_datetime(evaluation["timestamp_utc"], utc=True).dt.tz_convert(
        "America/Chicago"
    ).dt.date
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
    report = {
        "candidate_passed_all_gates": all(gates.values()),
        "gates": gates,
        "pinball_skill_vs_month_hour_climatology": skill,
        "coverage_absolute_error": coverage_error,
        "q50_mae_mw": float(mean_absolute_error(y_eval, predictions["q50"])),
        "baseline": baseline_metrics,
        "model": model_metrics,
        "known_limitations": [
            "Historical training uses ERA5 realized target-hour weather; production uses a one-hour weather forecast.",
            "No lagged-load features are used until an operational feature store exists.",
            "WIS is unavailable because the served artifact contains upper quantiles only.",
            (
                f"Annual demand growth is extrapolated log-linearly from pre-{evaluation_year} "
                "years and may miss structural breaks."
            ),
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
    parser.add_argument(
        "--model-version",
        default="ercot-trend-conformal-gbt-v1.2.0-candidate",
    )
    args = parser.parse_args()
    report = train(
        args.features,
        args.artifact_dir,
        evaluation_year=args.evaluation_year,
        model_version=args.model_version,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
