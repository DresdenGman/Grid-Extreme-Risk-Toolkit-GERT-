"""
Model artifact contract: schema definitions, validation, and loader.

Defines the required structure for trained model artifacts that can be
loaded by RealModelAdapter. No training is performed here.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class ModelArtifactError(RuntimeError):
    """Raised when a model artifact is missing, invalid, or incompatible."""


# ---------------------------------------------------------------------------
#  Immutable schema types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrainingPeriod:
    start: str  # ISO-8601 date
    end: str    # ISO-8601 date


@dataclass(frozen=True)
class ForecastContract:
    forecast_origin: str
    target_horizon_hours: int
    target_variable: str


@dataclass(frozen=True)
class ModelRuntime:
    python_version: str
    scikit_learn_version: str


@dataclass(frozen=True)
class ModelMetadata:
    artifact_schema_version: str
    model_name: str
    model_version: str
    model_type: str
    created_at: str
    training_period: TrainingPeriod
    forecast_contract: ForecastContract
    feature_names: List[str]
    feature_units: Dict[str, str]
    quantiles: List[float]
    supported_regions: List[str]
    training_data: Dict[str, str]
    runtime: ModelRuntime
    validation_status: str


@dataclass(frozen=True)
class ModelMetrics:
    evaluation_period: Dict[str, str]
    sample_count: int
    pinball_loss: Dict[str, Optional[float]]
    empirical_coverage: Dict[str, Optional[float]]
    wis: Optional[float]
    quantile_crossing_rate: Optional[float]


@dataclass(frozen=True)
class LoadedModelArtifact:
    """Result of loading a validated artifact bundle."""
    metadata: ModelMetadata
    metrics: ModelMetrics
    model_path: Path


# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------

SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1", "1.2", "1.3"}
SUPPORTED_MODEL_TYPE = "sklearn_quantile_bundle"
FEATURES_BY_SCHEMA = {
    "1.0": ["temperature", "wind_speed", "solar_irradiance"],
    "1.1": [
        "temperature", "wind_speed", "solar_irradiance",
        "hour", "day_of_week", "month", "is_weekend",
    ],
    "1.2": [
        "temperature", "wind_speed", "solar_irradiance",
        "hour", "day_of_week", "month", "is_weekend", "year",
    ],
    "1.3": [
        "temperature", "wind_speed", "solar_irradiance",
        "hour", "day_of_week", "month", "is_weekend", "year",
        "lag_load_1h", "lag_load_24h", "lag_load_168h",
        "rolling_load_mean_24h", "rolling_load_std_24h",
        "rolling_load_mean_168h", "rolling_load_std_168h",
    ],
}
EXPECTED_QUANTILES = [0.5, 0.9, 0.95, 0.99]
BASE_FEATURE_UNITS = {
    "temperature": "degC",
    "wind_speed": "m/s",
    "solar_irradiance": "W/m2",
}
FEATURE_UNITS_BY_SCHEMA = {
    "1.0": BASE_FEATURE_UNITS,
    "1.1": {
        **BASE_FEATURE_UNITS,
        "hour": "local_hour",
        "day_of_week": "integer_0_monday",
        "month": "integer_1_january",
        "is_weekend": "binary",
    },
    "1.2": {
        **BASE_FEATURE_UNITS,
        "hour": "local_hour",
        "day_of_week": "integer_0_monday",
        "month": "integer_1_january",
        "is_weekend": "binary",
        "year": "ercot_local_year",
    },
    "1.3": {
        **BASE_FEATURE_UNITS,
        "hour": "local_hour",
        "day_of_week": "integer_0_monday",
        "month": "integer_1_january",
        "is_weekend": "binary",
        "year": "ercot_local_year",
        "lag_load_1h": "MW",
        "lag_load_24h": "MW",
        "lag_load_168h": "MW",
        "rolling_load_mean_24h": "MW",
        "rolling_load_std_24h": "MW",
        "rolling_load_mean_168h": "MW",
        "rolling_load_std_168h": "MW",
    },
}
ALLOWED_REGIONS = {"ERCOT_SYSTEM", "ERCOT_NORTH", "CAISO", "PJM", "NYISO"}
ALLOWED_VALIDATION_STATUSES = {
    "legacy_candidate",
    "provisional_candidate",
    "validated_production",
    "rejected_candidate",
}
REQUIRED_PROVENANCE_KEYS = {"source", "provenance"}
REQUIRED_RUNTIME_KEYS = {"python_version", "scikit_learn_version"}
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


# ---------------------------------------------------------------------------
#  Validation helpers
# ---------------------------------------------------------------------------


def _validate_not_empty(value: str, field: str) -> None:
    if not value or not value.strip():
        raise ModelArtifactError(f"'{field}' must be non-empty.")


def _validate_iso_date(value: str, field: str) -> None:
    if not ISO_DATE_RE.match(str(value)):
        raise ModelArtifactError(
            f"'{field}' must be an ISO-8601 date (YYYY-MM-DD), got: {value}"
        )


def _validate_quantile_metric_entry(name: str, d: Any) -> None:
    """Validate a metric dict has exactly q50/q90/q95/q99 keys with numeric or null."""
    if not isinstance(d, dict):
        raise ModelArtifactError(f"'{name}' must be a dict, got {type(d).__name__}")
    for q in ("q50", "q90", "q95", "q99"):
        if q not in d:
            raise ModelArtifactError(f"'{name}' missing required key '{q}'")
        val = d[q]
        if val is not None:
            try:
                float(val)
            except (TypeError, ValueError):
                raise ModelArtifactError(
                    f"'{name}.{q}' must be numeric or null, got {val!r}"
                )


# ---------------------------------------------------------------------------
#  Public validation
# ---------------------------------------------------------------------------


def validate_metadata(raw: dict) -> ModelMetadata:
    """Validate and return a ModelMetadata from raw dict.

    Raises ModelArtifactError on any invalid or missing field.
    """
    # 1. Schema version
    version = raw.get("artifact_schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ModelArtifactError(
            f"Unsupported artifact_schema_version: {version!r}. "
            f"Expected one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}."
        )

    # 2. Model name & version
    model_name = raw.get("model_name", "")
    _validate_not_empty(model_name, "model_name")
    model_version = raw.get("model_version", "")
    _validate_not_empty(model_version, "model_version")

    # 3. Model type
    model_type = raw.get("model_type")
    if model_type != SUPPORTED_MODEL_TYPE:
        raise ModelArtifactError(
            f"Unsupported model_type: {model_type!r}. "
            f"Expected '{SUPPORTED_MODEL_TYPE}'."
        )

    # 4. Created at
    created_at = raw.get("created_at", "")
    _validate_not_empty(created_at, "created_at")

    # 5. Training period
    tp = raw.get("training_period", {})
    if not isinstance(tp, dict) or "start" not in tp or "end" not in tp:
        raise ModelArtifactError(
            "training_period must be a dict with 'start' and 'end' keys."
        )
    _validate_iso_date(tp["start"], "training_period.start")
    _validate_iso_date(tp["end"], "training_period.end")
    if tp["start"] > tp["end"]:
        raise ModelArtifactError(
            f"training_period.start ({tp['start']}) > "
            f"training_period.end ({tp['end']})"
        )

    # 6. Forecast contract
    fc = raw.get("forecast_contract", {})
    if not isinstance(fc, dict):
        raise ModelArtifactError("forecast_contract must be a dict.")
    if fc.get("forecast_origin") != "request_time":
        raise ModelArtifactError(
            f"forecast_contract.forecast_origin must be 'request_time', "
            f"got {fc.get('forecast_origin')!r}"
        )
    try:
        horizon = int(fc["target_horizon_hours"])
    except (KeyError, ValueError, TypeError):
        raise ModelArtifactError(
            "forecast_contract.target_horizon_hours must be a positive integer."
        )
    if horizon <= 0:
        raise ModelArtifactError(
            f"forecast_contract.target_horizon_hours must be positive, got {horizon}."
        )
    if fc.get("target_variable") != "grid_load_mw":
        raise ModelArtifactError(
            f"forecast_contract.target_variable must be 'grid_load_mw', "
            f"got {fc.get('target_variable')!r}"
        )

    # 7. Feature names
    features = raw.get("feature_names", [])
    expected_features = FEATURES_BY_SCHEMA[version]
    if features != expected_features:
        raise ModelArtifactError(
            f"Expected feature_names={expected_features}, got {features}"
        )

    # 8. Feature units
    units = raw.get("feature_units", {})
    if not isinstance(units, dict):
        raise ModelArtifactError("feature_units must be a dict.")
    expected_units = FEATURE_UNITS_BY_SCHEMA[version]
    if units != expected_units:
        raise ModelArtifactError(
            f"Expected feature_units={expected_units}, got {units}"
        )

    # 9. Quantiles
    quantiles = sorted(raw.get("quantiles", []))
    if quantiles != sorted(EXPECTED_QUANTILES):
        raise ModelArtifactError(
            f"Expected sorted quantiles={sorted(EXPECTED_QUANTILES)}, "
            f"got {quantiles}"
        )

    # 10. Supported regions
    regions = raw.get("supported_regions", [])
    if not isinstance(regions, list) or len(regions) == 0:
        raise ModelArtifactError("supported_regions must be a non-empty list.")
    seen = set()
    for r in regions:
        if r in seen:
            raise ModelArtifactError(
                f"Duplicate region in supported_regions: {r}"
            )
        if r not in ALLOWED_REGIONS:
            raise ModelArtifactError(
                f"Unsupported region: {r!r}. "
                f"Allowed: {sorted(ALLOWED_REGIONS)}"
            )
        seen.add(r)

    # 11. Training provenance
    td = raw.get("training_data", {})
    if not isinstance(td, dict):
        raise ModelArtifactError("training_data must be a dict.")
    missing_prov = REQUIRED_PROVENANCE_KEYS - set(td.keys())
    if missing_prov:
        raise ModelArtifactError(
            f"training_data missing required keys: {missing_prov}"
        )

    # 12. Runtime fields
    rt = raw.get("runtime", {})
    if not isinstance(rt, dict):
        raise ModelArtifactError("runtime must be a dict.")
    missing_rt = REQUIRED_RUNTIME_KEYS - set(rt.keys())
    if missing_rt:
        raise ModelArtifactError(
            f"runtime missing required keys: {missing_rt}"
        )

    validation_status = raw.get("validation_status", "legacy_candidate")
    if validation_status not in ALLOWED_VALIDATION_STATUSES:
        raise ModelArtifactError(
            f"Unsupported validation_status: {validation_status!r}"
        )

    return ModelMetadata(
        artifact_schema_version=version,
        model_name=model_name,
        model_version=model_version,
        model_type=model_type,
        created_at=created_at,
        training_period=TrainingPeriod(start=tp["start"], end=tp["end"]),
        forecast_contract=ForecastContract(
            forecast_origin=fc["forecast_origin"],
            target_horizon_hours=horizon,
            target_variable=fc["target_variable"],
        ),
        feature_names=features,
        feature_units=units,
        quantiles=quantiles,
        supported_regions=regions,
        training_data=td,
        runtime=ModelRuntime(
            python_version=rt.get("python_version", "UNSPECIFIED"),
            scikit_learn_version=rt.get("scikit_learn_version", "UNSPECIFIED"),
        ),
        validation_status=validation_status,
    )


def validate_metrics(raw: dict) -> ModelMetrics:
    """Validate metrics dict and return a ModelMetrics.

    Raises ModelArtifactError on any invalid field.
    """
    ep = raw.get("evaluation_period", {})
    if not isinstance(ep, dict):
        raise ModelArtifactError("evaluation_period must be a dict.")
    if "start" in ep and "end" in ep:
        _validate_iso_date(ep["start"], "evaluation_period.start")
        _validate_iso_date(ep["end"], "evaluation_period.end")
        if ep["start"] > ep["end"]:
            raise ModelArtifactError(
                f"evaluation_period.start ({ep['start']}) > "
                f"evaluation_period.end ({ep['end']})"
            )

    sample_count = raw.get("sample_count", 0)
    if not isinstance(sample_count, int) or sample_count < 0:
        raise ModelArtifactError(
            f"sample_count must be a non-negative integer, got {sample_count!r}."
        )

    pinball = raw.get("pinball_loss", {})
    _validate_quantile_metric_entry("pinball_loss", pinball)

    coverage = raw.get("empirical_coverage", {})
    _validate_quantile_metric_entry("empirical_coverage", coverage)
    for q_key in ("q50", "q90", "q95", "q99"):
        val = coverage.get(q_key)
        if val is not None and not (0 <= float(val) <= 1):
            raise ModelArtifactError(
                f"empirical_coverage.{q_key} must be in [0, 1] or null, "
                f"got {val!r}."
            )

    wis = raw.get("wis")
    if wis is not None:
        try:
            float(wis)
        except (TypeError, ValueError):
            raise ModelArtifactError(f"wis must be numeric or null, got {wis!r}.")

    crossing = raw.get("quantile_crossing_rate")
    if crossing is not None:
        try:
            cv = float(crossing)
        except (TypeError, ValueError):
            raise ModelArtifactError(
                f"quantile_crossing_rate must be numeric or null, got {crossing!r}."
            )
        if not (0 <= cv <= 1):
            raise ModelArtifactError(
                f"quantile_crossing_rate must be in [0, 1] or null, got {cv!r}."
            )

    return ModelMetrics(
        evaluation_period=ep,
        sample_count=sample_count,
        pinball_loss={k: pinball.get(k) for k in ("q50", "q90", "q95", "q99")},
        empirical_coverage={k: coverage.get(k) for k in ("q50", "q90", "q95", "q99")},
        wis=float(wis) if wis is not None else None,
        quantile_crossing_rate=float(crossing) if crossing is not None else None,
    )


def _validate_estimator_bundle(artifact_dir: Path, model_path: Path) -> None:
    """Validate the persisted model can be loaded and has the right interface.

    Accepts:
    - An object with callable predict_quantiles, or
    - A dict with keys q50/q90/q95/q99, each a callable with predict().

    Does NOT invoke predictions.
    """
    import joblib

    try:
        obj = joblib.load(model_path)
    except Exception as exc:
        raise ModelArtifactError(
            f"Failed to load model at {model_path}: {exc}"
        )

    # Case 1: object with predict_quantiles
    if hasattr(obj, "predict_quantiles") and callable(obj.predict_quantiles):
        return

    # Case 2: mapping with quantile keys
    if isinstance(obj, dict):
        for q_key in ("q50", "q90", "q95", "q99"):
            if q_key not in obj:
                raise ModelArtifactError(
                    f"Mapping bundle missing key '{q_key}'."
                )
            estimator = obj[q_key]
            if not hasattr(estimator, "predict") or not callable(estimator.predict):
                raise ModelArtifactError(
                    f"Mapping bundle key '{q_key}' does not have callable predict()."
                )
        extra = set(obj.keys()) - {"q50", "q90", "q95", "q99"}
        if extra:
            raise ModelArtifactError(
                f"Mapping bundle has unexpected keys: {extra}. "
                "Allowed: q50, q90, q95, q99."
            )
        return

    raise ModelArtifactError(
        f"Unsupported model type: {type(obj).__name__}. "
        "Expected object with predict_quantiles() or "
        "dict with q50/q90/q95/q99 estimators."
    )


# ---------------------------------------------------------------------------
#  Public loader
# ---------------------------------------------------------------------------


def load_model_artifact(artifact_dir: Path) -> LoadedModelArtifact:
    """Load and validate a model artifact bundle from a directory.

    Expected structure::

        artifact_dir/
            metadata.json      (required)
            metrics.json       (required)
            model.joblib       (required)

    Raises ModelArtifactError on any validation failure.
    """
    base = Path(artifact_dir)
    if not base.is_dir():
        raise ModelArtifactError(
            f"Artifact directory not found: {artifact_dir}"
        )

    meta_path = base / "metadata.json"
    if not meta_path.is_file():
        raise ModelArtifactError(
            f"Missing required file: {meta_path}"
        )

    metrics_path = base / "metrics.json"
    if not metrics_path.is_file():
        raise ModelArtifactError(
            f"Missing required file: {metrics_path}"
        )

    model_path = base / "model.joblib"
    if not model_path.is_file():
        raise ModelArtifactError(
            f"Missing required file: {model_path}"
        )

    # Validate metadata
    try:
        with open(meta_path) as f:
            meta_raw = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise ModelArtifactError(
            f"Invalid or unreadable metadata.json: {exc}"
        )
    metadata = validate_metadata(meta_raw)

    # Validate metrics
    try:
        with open(metrics_path) as f:
            metrics_raw = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise ModelArtifactError(
            f"Invalid or unreadable metrics.json: {exc}"
        )
    metrics = validate_metrics(metrics_raw)

    # Validate serialized bundle
    _validate_estimator_bundle(base, model_path)

    return LoadedModelArtifact(
        metadata=metadata,
        metrics=metrics,
        model_path=model_path,
    )
