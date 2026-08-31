"""Expanded tests for model artifact contract (models/artifacts.py)."""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from models.artifacts import (
    ModelArtifactError,
    ModelMetadata,
    ModelMetrics,
    validate_metadata,
    validate_metrics,
    load_model_artifact,
    LoadedModelArtifact,
)


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_metadata_dict():
    return {
        "artifact_schema_version": "1.0",
        "model_name": "gert_weather_quantile",
        "model_version": "0.1.0",
        "model_type": "sklearn_quantile_bundle",
        "created_at": "2026-07-27T00:00:00Z",
        "training_period": {"start": "2026-01-01", "end": "2026-06-30"},
        "forecast_contract": {
            "forecast_origin": "request_time",
            "target_horizon_hours": 1,
            "target_variable": "grid_load_mw",
        },
        "feature_names": ["temperature", "wind_speed", "solar_irradiance"],
        "feature_units": {
            "temperature": "degC",
            "wind_speed": "m/s",
            "solar_irradiance": "W/m2",
        },
        "quantiles": [0.5, 0.9, 0.95, 0.99],
        "supported_regions": ["ERCOT_NORTH", "CAISO", "PJM", "NYISO"],
        "training_data": {"source": "TEST", "provenance": "TEST"},
        "runtime": {
            "python_version": "3.11.15",
            "scikit_learn_version": "1.7.2",
        },
    }


@pytest.fixture
def valid_metrics_dict():
    return {
        "evaluation_period": {"start": "2026-01-01", "end": "2026-06-30"},
        "sample_count": 1000,
        "pinball_loss": {"q50": 100.0, "q90": 200.0, "q95": 300.0, "q99": 400.0},
        "empirical_coverage": {"q50": 0.5, "q90": 0.89, "q95": 0.94, "q99": 0.99},
        "wis": 250.0,
        "quantile_crossing_rate": 0.0,
    }


class _DummyPredictor:
    """A picklable class that satisfies the model interface."""
    def predict_quantiles(self, features):
        return {"q50": 0, "q90": 0, "q95": 0, "q99": 0}


@pytest.fixture
def artifact_dir(valid_metadata_dict, valid_metrics_dict):
    """Build a temporary directory with valid artifact files."""
    import pickle
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "metadata.json").write_text(json.dumps(valid_metadata_dict))
        (p / "metrics.json").write_text(json.dumps(valid_metrics_dict))
        (p / "model.joblib").write_bytes(pickle.dumps(_DummyPredictor()))
        yield str(p)


# ---------------------------------------------------------------------------
#  Validate Metadata
# ---------------------------------------------------------------------------


class TestValidateMetadata:
    def test_valid(self, valid_metadata_dict):
        meta = validate_metadata(valid_metadata_dict)
        assert isinstance(meta, ModelMetadata)
        assert meta.model_name == "gert_weather_quantile"

    def test_schema_1_1_calendar_features(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["artifact_schema_version"] = "1.1"
        d["feature_names"] = [
            "temperature", "wind_speed", "solar_irradiance",
            "hour", "day_of_week", "month", "is_weekend",
        ]
        d["feature_units"] = {
            "temperature": "degC", "wind_speed": "m/s", "solar_irradiance": "W/m2",
            "hour": "local_hour", "day_of_week": "integer_0_monday",
            "month": "integer_1_january", "is_weekend": "binary",
        }
        assert validate_metadata(d).artifact_schema_version == "1.1"

    def test_schema_1_3_operational_features(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["artifact_schema_version"] = "1.3"
        d["feature_names"] = [
            "temperature", "wind_speed", "solar_irradiance",
            "hour", "day_of_week", "month", "is_weekend", "year",
            "lag_load_1h", "lag_load_24h", "lag_load_168h",
            "rolling_load_mean_24h", "rolling_load_std_24h",
            "rolling_load_mean_168h", "rolling_load_std_168h",
        ]
        d["feature_units"] = {
            "temperature": "degC", "wind_speed": "m/s", "solar_irradiance": "W/m2",
            "hour": "local_hour", "day_of_week": "integer_0_monday",
            "month": "integer_1_january", "is_weekend": "binary",
            "year": "ercot_local_year",
            "lag_load_1h": "MW", "lag_load_24h": "MW", "lag_load_168h": "MW",
            "rolling_load_mean_24h": "MW", "rolling_load_std_24h": "MW",
            "rolling_load_mean_168h": "MW", "rolling_load_std_168h": "MW",
        }
        assert validate_metadata(d).artifact_schema_version == "1.3"

    def test_unsupported_schema_version(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["artifact_schema_version"] = "0.9"
        with pytest.raises(ModelArtifactError, match="Unsupported.*schema"):
            validate_metadata(d)

    def test_blank_model_name(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["model_name"] = ""
        with pytest.raises(ModelArtifactError, match="model_name"):
            validate_metadata(d)

    def test_blank_model_version(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["model_version"] = ""
        with pytest.raises(ModelArtifactError, match="model_version"):
            validate_metadata(d)

    def test_wrong_model_type(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["model_type"] = "random_forest"
        with pytest.raises(ModelArtifactError, match="Unsupported.*model_type"):
            validate_metadata(d)

    def test_missing_training_period_keys(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["training_period"] = {}
        with pytest.raises(ModelArtifactError, match="training_period"):
            validate_metadata(d)

    def test_reversed_training_period(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["training_period"] = {"start": "2026-06-30", "end": "2026-01-01"}
        with pytest.raises(ModelArtifactError, match="start.*>.*end"):
            validate_metadata(d)

    def test_wrong_forecast_origin(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["forecast_contract"]["forecast_origin"] = "real_time"
        with pytest.raises(ModelArtifactError, match="forecast_origin"):
            validate_metadata(d)

    def test_zero_horizon(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["forecast_contract"]["target_horizon_hours"] = 0
        with pytest.raises(ModelArtifactError, match="target_horizon_hours"):
            validate_metadata(d)

    def test_negative_horizon(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["forecast_contract"]["target_horizon_hours"] = -1
        with pytest.raises(ModelArtifactError, match="target_horizon_hours"):
            validate_metadata(d)

    def test_wrong_target_variable(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["forecast_contract"]["target_variable"] = "price"
        with pytest.raises(ModelArtifactError, match="target_variable"):
            validate_metadata(d)

    def test_wrong_feature_names(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["feature_names"] = ["temperature"]
        with pytest.raises(ModelArtifactError, match="Expected feature_names"):
            validate_metadata(d)

    def test_wrong_feature_units(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["feature_units"]["temperature"] = "F"
        with pytest.raises(ModelArtifactError, match="feature_units"):
            validate_metadata(d)

    def test_wrong_quantiles(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["quantiles"] = [0.01, 0.99]
        with pytest.raises(ModelArtifactError, match="Expected sorted quantiles"):
            validate_metadata(d)

    def test_unsupported_region(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["supported_regions"] = ["ERCOT_NORTH", "SPP"]
        with pytest.raises(ModelArtifactError, match="Unsupported region"):
            validate_metadata(d)

    def test_duplicate_region(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["supported_regions"] = ["ERCOT_NORTH", "ERCOT_NORTH"]
        with pytest.raises(ModelArtifactError, match="Duplicate region"):
            validate_metadata(d)

    def test_missing_provenance(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        del d["training_data"]
        with pytest.raises(ModelArtifactError, match="training_data"):
            validate_metadata(d)

    def test_missing_runtime_fields(self, valid_metadata_dict):
        d = dict(valid_metadata_dict)
        d["runtime"] = {}
        with pytest.raises(ModelArtifactError, match="runtime.*missing"):
            validate_metadata(d)


# ---------------------------------------------------------------------------
#  Validate Metrics
# ---------------------------------------------------------------------------


class TestValidateMetrics:
    def test_valid(self, valid_metrics_dict):
        m = validate_metrics(valid_metrics_dict)
        assert isinstance(m, ModelMetrics)
        assert m.sample_count == 1000

    def test_null_values_accepted(self, valid_metrics_dict):
        d = dict(valid_metrics_dict)
        d["wis"] = None
        d["quantile_crossing_rate"] = None
        m = validate_metrics(d)
        assert m.wis is None
        assert m.quantile_crossing_rate is None

    def test_negative_sample_count(self, valid_metrics_dict):
        d = dict(valid_metrics_dict)
        d["sample_count"] = -1
        with pytest.raises(ModelArtifactError, match="sample_count"):
            validate_metrics(d)

    def test_coverage_above_1(self, valid_metrics_dict):
        d = dict(valid_metrics_dict)
        d["empirical_coverage"]["q99"] = 1.1
        with pytest.raises(ModelArtifactError, match="empirical_coverage.*q99"):
            validate_metrics(d)

    def test_crossing_below_0(self, valid_metrics_dict):
        d = dict(valid_metrics_dict)
        d["quantile_crossing_rate"] = -0.1
        with pytest.raises(ModelArtifactError, match="quantile_crossing_rate"):
            validate_metrics(d)

    def test_crossing_above_1(self, valid_metrics_dict):
        d = dict(valid_metrics_dict)
        d["quantile_crossing_rate"] = 1.5
        with pytest.raises(ModelArtifactError, match="quantile_crossing_rate"):
            validate_metrics(d)

    def test_missing_q50_in_pinball(self, valid_metrics_dict):
        d = dict(valid_metrics_dict)
        del d["pinball_loss"]["q50"]
        with pytest.raises(ModelArtifactError, match="pinball_loss.*missing.*q50"):
            validate_metrics(d)

    def test_missing_q99_in_coverage(self, valid_metrics_dict):
        d = dict(valid_metrics_dict)
        del d["empirical_coverage"]["q99"]
        with pytest.raises(ModelArtifactError, match="empirical_coverage.*missing.*q99"):
            validate_metrics(d)

    def test_reversed_evaluation_period(self, valid_metrics_dict):
        d = dict(valid_metrics_dict)
        d["evaluation_period"] = {"start": "2026-06-30", "end": "2026-01-01"}
        with pytest.raises(ModelArtifactError, match="evaluation_period"):
            validate_metrics(d)

    def test_nonnumeric_pinball(self, valid_metrics_dict):
        d = dict(valid_metrics_dict)
        d["pinball_loss"]["q50"] = "bad"
        with pytest.raises(ModelArtifactError, match="pinball_loss"):
            validate_metrics(d)


# ---------------------------------------------------------------------------
#  Load Artifact
# ---------------------------------------------------------------------------


class TestLoadArtifact:
    def test_directory_not_found(self):
        with pytest.raises(ModelArtifactError, match="not found"):
            load_model_artifact(Path("/nonexistent/path"))

    def test_missing_metadata(self, tmp_path):
        (tmp_path / "metrics.json").write_text("{}")
        (tmp_path / "model.joblib").write_text("dummy")
        with pytest.raises(ModelArtifactError, match="metadata.json"):
            load_model_artifact(tmp_path)

    def test_missing_metrics(self, tmp_path):
        (tmp_path / "metadata.json").write_text('{"artifact_schema_version":"1.0"}')
        (tmp_path / "model.joblib").write_text("dummy")
        with pytest.raises(ModelArtifactError, match="metrics.json"):
            load_model_artifact(tmp_path)

    def test_missing_model(self, tmp_path):
        (tmp_path / "metadata.json").write_text('{"artifact_schema_version":"1.0"}')
        (tmp_path / "metrics.json").write_text("{}")
        with pytest.raises(ModelArtifactError, match="model.joblib"):
            load_model_artifact(tmp_path)

    def test_malformed_metadata_json(self, tmp_path):
        (tmp_path / "metadata.json").write_text("not json")
        (tmp_path / "metrics.json").write_text("{}")
        (tmp_path / "model.joblib").write_text("dummy")
        with pytest.raises(ModelArtifactError, match="metadata.json"):
            load_model_artifact(tmp_path)

    def test_malformed_metrics_json(self, tmp_path, artifact_dir):
        p = Path(artifact_dir)
        (p / "metrics.json").write_text("not json")
        with pytest.raises(ModelArtifactError, match="metrics.json"):
            load_model_artifact(p)

    def test_valid_artifact(self, artifact_dir):
        result = load_model_artifact(Path(artifact_dir))
        assert isinstance(result, LoadedModelArtifact)
        assert result.metadata.model_name == "gert_weather_quantile"

    def test_with_metrics(self, artifact_dir):
        result = load_model_artifact(Path(artifact_dir))
        assert result.metrics is not None
        assert result.metrics.wis == 250.0
        assert result.metrics.quantile_crossing_rate == 0.0


# ---------------------------------------------------------------------------
#  Estimator bundle validation (unit only, no real bundled model)
# ---------------------------------------------------------------------------


class _DummyEstimator:
    """Picklable callable with predict()."""
    def predict(self, X):
        return [0] * len(X)


class _PlainObject:
    """A plain object with no model interface."""
    pass


class TestEstimatorBundleValidation:
    """Test _validate_estimator_bundle indirectly via load_model_artifact."""

    def test_invalid_object_rejected(self, tmp_path, valid_metadata_dict,
                                     valid_metrics_dict):
        """A pickle that isn't a model should be rejected."""
        import pickle
        (tmp_path / "metadata.json").write_text(json.dumps(valid_metadata_dict))
        (tmp_path / "metrics.json").write_text(json.dumps(valid_metrics_dict))
        # Pickle a plain object (no predict_quantiles, not a mapping with 4 keys)
        (tmp_path / "model.joblib").write_bytes(pickle.dumps(_PlainObject()))
        with pytest.raises(ModelArtifactError, match="Unsupported model type"):
            load_model_artifact(tmp_path)

    def test_mapping_missing_q99(self, tmp_path, valid_metadata_dict,
                                  valid_metrics_dict):
        import pickle
        (tmp_path / "metadata.json").write_text(json.dumps(valid_metadata_dict))
        (tmp_path / "metrics.json").write_text(json.dumps(valid_metrics_dict))
        # dict with 3 of 4 required keys
        obj = {"q50": _DummyEstimator(), "q90": _DummyEstimator(),
               "q95": _DummyEstimator()}
        (tmp_path / "model.joblib").write_bytes(pickle.dumps(obj))
        with pytest.raises(ModelArtifactError, match="missing key.*q99"):
            load_model_artifact(tmp_path)

    def test_mapping_with_extra_key(self, tmp_path, valid_metadata_dict,
                                     valid_metrics_dict):
        import pickle
        (tmp_path / "metadata.json").write_text(json.dumps(valid_metadata_dict))
        (tmp_path / "metrics.json").write_text(json.dumps(valid_metrics_dict))
        obj = {"q50": _DummyEstimator(), "q90": _DummyEstimator(),
               "q95": _DummyEstimator(), "q99": _DummyEstimator(),
               "extra": _DummyEstimator()}
        (tmp_path / "model.joblib").write_bytes(pickle.dumps(obj))
        with pytest.raises(ModelArtifactError, match="unexpected keys"):
            load_model_artifact(tmp_path)
