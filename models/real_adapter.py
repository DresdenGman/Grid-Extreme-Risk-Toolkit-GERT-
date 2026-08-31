"""Real model adapter — loads a trained artifact bundle via the artifact contract."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping
from zoneinfo import ZoneInfo

import numpy as np

from api.schemas import WeatherFeatures
from models.artifacts import (
    ModelArtifactError,
    ModelMetadata,
    load_model_artifact,
    LoadedModelArtifact,
)
from models.interfaces import ModelInterface
from models.quantiles import enforce_quantile_monotonicity

logger = logging.getLogger("gert_backend")


class RealModelAdapter(ModelInterface):
    """Loads a versioned artifact bundle and serves predictions.

    Instantiation requires ``MODEL_ARTIFACT_DIR`` to be set and to point
    at a directory containing ``metadata.json``, ``metrics.json``, and
    ``model.joblib`` conforming to the artifact schema.
    """

    def __init__(
        self,
        artifact_dir: str | None = None,
    ) -> None:
        env_dir = artifact_dir or os.getenv("MODEL_ARTIFACT_DIR")
        if not env_dir or not env_dir.strip():
            raise RuntimeError(
                "MODEL_ARTIFACT_DIR is required when MODEL_BACKEND=real, "
                "but is unset or empty."
            )

        path = Path(env_dir.strip())
        if not path.is_absolute():
            raise RuntimeError(
                f"MODEL_ARTIFACT_DIR must be an absolute path, got: {env_dir}"
            )

        self._loaded: LoadedModelArtifact = load_model_artifact(path)
        self._artifact_dir = path
        self._meta: ModelMetadata = self._loaded.metadata
        self._bundle: Any = _lazy_load_bundle(self._loaded.model_path)

        logger.info(
            "RealModelAdapter initialized",
            extra={
                "model_name": self._meta.model_name,
                "model_version": self._meta.model_version,
                "artifact_path": str(path),
            },
        )

    def get_version(self) -> str:
        return self._meta.model_version

    def supports_region(self, region: str) -> bool:
        return region in self._meta.supported_regions

    def get_evaluation_metrics(self):
        return self._loaded.metrics

    @property
    def validation_status(self) -> str:
        return self._meta.validation_status

    @property
    def requires_operational_features(self) -> bool:
        return self._meta.artifact_schema_version == "1.3"

    def get_artifact_file(self, name: str) -> Path:
        if Path(name).name != name:
            raise ValueError("Artifact filename must not contain a path")
        return self._artifact_dir / name

    def predict(
        self,
        features: WeatherFeatures,
        timestamp: datetime | None = None,
        operational_features: Mapping[str, float] | None = None,
    ) -> Dict[str, float]:
        values: dict[str, float] = {
            "temperature": features.temperature,
            "wind_speed": features.wind_speed,
            "solar_irradiance": features.solar_irradiance,
        }
        if self._meta.artifact_schema_version in {"1.1", "1.2", "1.3"}:
            effective = timestamp or datetime.now(timezone.utc)
            if effective.tzinfo is None:
                effective = effective.replace(tzinfo=timezone.utc)
            local = effective.astimezone(ZoneInfo("America/Chicago"))
            values.update(
                {
                    "hour": float(local.hour),
                    "day_of_week": float(local.weekday()),
                    "month": float(local.month),
                    "is_weekend": float(local.weekday() >= 5),
                }
            )
            if self._meta.artifact_schema_version in {"1.2", "1.3"}:
                values["year"] = float(local.year)
        if self._meta.artifact_schema_version == "1.3":
            required = set(self._meta.feature_names) - set(values)
            if operational_features is None:
                raise ModelArtifactError(
                    "Schema 1.3 requires server-supplied operational load features."
                )
            missing = sorted(required - set(operational_features))
            if missing:
                raise ModelArtifactError(
                    f"Operational feature context is missing: {missing}"
                )
            for name in required:
                value = float(operational_features[name])
                if not np.isfinite(value):
                    raise ModelArtifactError(
                        f"Operational feature '{name}' must be finite."
                    )
                values[name] = value
        feature_row = [values[name] for name in self._meta.feature_names]

        try:
            if hasattr(self._bundle, "predict_quantiles"):
                raw = self._bundle.predict_quantiles([feature_row])
            elif isinstance(self._bundle, dict):
                raw = {
                    key: estimator.predict([feature_row])
                    for key, estimator in self._bundle.items()
                }
            else:
                raise ModelArtifactError(
                    f"Unsupported bundle type: {type(self._bundle).__name__}."
                )
        except ModelArtifactError:
            raise
        except Exception as exc:
            raise ModelArtifactError(
                f"Prediction failed for model {self._meta.model_version}: "
                f"{exc}"
            ) from exc

        result = _normalize_quantile_output(raw)

        # Detect and correct quantile crossing
        corrected = enforce_quantile_monotonicity(result)
        if corrected != result:
            logger.warning(
                "Quantile crossing corrected in prediction",
                extra={
                    "model_version": self._meta.model_version,
                    "before": result,
                    "after": corrected,
                },
            )

        return corrected


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------


def _lazy_load_bundle(model_path: Path) -> Any:
    """Load the serialized model bundle from disk."""
    import joblib

    try:
        obj = joblib.load(model_path)
    except Exception as exc:
        raise ModelArtifactError(
            f"Failed to load model at {model_path}: {exc}"
        ) from exc
    return obj


def _extract_scalar(value: Any) -> float:
    """Reduce a prediction output to a single float, or raise."""
    if isinstance(value, bool):
        raise ModelArtifactError(
            f"Prediction output is boolean ({value}), not a numeric scalar."
        )

    if isinstance(value, (int, float)):
        return float(value)

    # List / tuple / ndarray …
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            raise ModelArtifactError("Prediction output is empty.")
        if len(value) > 1:
            raise ModelArtifactError(
                f"Prediction output has {len(value)} elements, expected exactly 1."
            )
        return _extract_scalar(value[0])

    # NumPy-like array
    if hasattr(value, "tolist"):
        return _extract_scalar(value.tolist())

    raise ModelArtifactError(
        f"Cannot convert prediction output to scalar: {type(value).__name__}"
    )


def _normalize_quantile_output(raw: Any) -> Dict[str, float]:
    """Normalise raw prediction output to ``{q50, q90, q95, q99}``."""
    expected_keys = {"q50", "q90", "q95", "q99"}

    if isinstance(raw, dict):
        actual_keys = set(raw.keys())
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        if missing:
            raise ModelArtifactError(
                f"Prediction output missing quantile keys: {sorted(missing)}"
            )
        if extra:
            raise ModelArtifactError(
                f"Prediction output has unexpected keys: {sorted(extra)}"
            )
        result: Dict[str, float] = {}
        for key in ("q50", "q90", "q95", "q99"):
            result[key] = _extract_scalar(raw[key])
        return result

    if hasattr(raw, "keys") and hasattr(raw, "__getitem__"):
        # Duck-type dict-like
        return _normalize_quantile_output(dict(raw))

    raise ModelArtifactError(
        f"Unrecognised prediction output type: {type(raw).__name__}. "
        "Expected dict with q50/q90/q95/q99."
    )


def _validate_finite(result: Dict[str, float]) -> None:
    """Check all values are finite numbers."""
    import math

    for key, value in result.items():
        if not isinstance(value, (int, float)):
            raise ModelArtifactError(
                f"Prediction output '{key}' is {type(value).__name__}, not numeric."
            )
        if math.isnan(value):
            raise ModelArtifactError(
                f"Prediction output '{key}' is NaN."
            )
        if math.isinf(value):
            raise ModelArtifactError(
                f"Prediction output '{key}' is infinite ({value})."
            )
