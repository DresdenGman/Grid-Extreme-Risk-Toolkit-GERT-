"""Integration tests for RealModelAdapter with artifact loading."""
import json
import os
import pickle
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from models.artifacts import ModelArtifactError
from models.real_adapter import RealModelAdapter
from models.stub import QuantileModelStub
from models.factory import get_model_service

from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


def _build_valid_artifact_dir():
    """Create a temp dir with valid artifact and return its path."""
    import tempfile
    tmp = tempfile.mkdtemp()
    p = Path(tmp)
    (p / "metadata.json").write_text(json.dumps(VALID_METADATA))
    (p / "metrics.json").write_text(json.dumps(VALID_METRICS))
    (p / "model.joblib").write_bytes(pickle.dumps(_PredictQuantilesObject()))
    return tmp


# ---------------------------------------------------------------------------
#  Helper — build a temporary valid artifact
# ---------------------------------------------------------------------------

VALID_METADATA = {
    "artifact_schema_version": "1.0",
    "model_name": "test_model",
    "model_version": "0.1.0-test",
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
        "temperature": "degC", "wind_speed": "m/s", "solar_irradiance": "W/m2",
    },
    "quantiles": [0.5, 0.9, 0.95, 0.99],
    "supported_regions": ["ERCOT_NORTH", "CAISO", "PJM", "NYISO"],
    "training_data": {"source": "TEST", "provenance": "TEST"},
    "runtime": {"python_version": "3.11", "scikit_learn_version": "1.7"},
}

VALID_METRICS = {
    "evaluation_period": {"start": "2026-01-01", "end": "2026-06-30"},
    "sample_count": 100,
    "pinball_loss": {"q50": 10, "q90": 20, "q95": 30, "q99": 40},
    "empirical_coverage": {"q50": 0.5, "q90": 0.9, "q95": 0.94, "q99": 0.99},
    "wis": 25.0,
    "quantile_crossing_rate": 0.0,
}


class _PredictQuantilesObject:
    """Object bundle: has callable predict_quantiles()."""
    def predict_quantiles(self, X):
        return {"q50": X[0][0] * 100, "q90": X[0][0] * 110,
                "q95": X[0][0] * 115, "q99": X[0][0] * 120}


class _Estimator:
    """Standalone estimator with callable predict()."""
    def __init__(self, multiplier=100):
        self.multiplier = multiplier
    def predict(self, X):
        return [X[0][0] * self.multiplier]


class _SumEstimator:
    def predict(self, X):
        return [sum(X[0])]


@pytest.fixture
def object_bundle_dir():
    """Temp dir with an object-bundle artifact."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "metadata.json").write_text(json.dumps(VALID_METADATA))
        (p / "metrics.json").write_text(json.dumps(VALID_METRICS))
        (p / "model.joblib").write_bytes(pickle.dumps(_PredictQuantilesObject()))
        yield str(p)


@pytest.fixture
def mapping_bundle_dir():
    """Temp dir with a mapping-bundle artifact."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "metadata.json").write_text(json.dumps(VALID_METADATA))
        (p / "metrics.json").write_text(json.dumps(VALID_METRICS))
        bundle = {k: _Estimator(m) for k, m in
                  [("q50", 100), ("q90", 110), ("q95", 115), ("q99", 120)]}
        (p / "model.joblib").write_bytes(pickle.dumps(bundle))
        yield str(p)


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------


class TestRealModelAdapter:
    def test_loads_object_bundle(self, object_bundle_dir):
        a = RealModelAdapter(artifact_dir=object_bundle_dir)
        assert a.get_version() == "0.1.0-test"

    def test_loads_mapping_bundle(self, mapping_bundle_dir):
        a = RealModelAdapter(artifact_dir=mapping_bundle_dir)
        assert a.get_version() == "0.1.0-test"

    def test_predict_object_bundle(self, object_bundle_dir):
        from api.schemas import WeatherFeatures
        a = RealModelAdapter(artifact_dir=object_bundle_dir)
        w = WeatherFeatures(temperature=25, wind_speed=10, solar_irradiance=500)
        r = a.predict(w)
        assert r["q99"] >= r["q95"] >= r["q90"] >= r["q50"]

    def test_predict_mapping_bundle(self, mapping_bundle_dir):
        from api.schemas import WeatherFeatures
        a = RealModelAdapter(artifact_dir=mapping_bundle_dir)
        w = WeatherFeatures(temperature=25, wind_speed=10, solar_irradiance=500)
        r = a.predict(w)
        assert r["q99"] >= r["q95"] >= r["q90"] >= r["q50"]

    def test_feature_order(self, mapping_bundle_dir):
        """temperature=25, wind_speed=10, solar=500 → [25, 10, 500]"""
        from api.schemas import WeatherFeatures
        a = RealModelAdapter(artifact_dir=mapping_bundle_dir)
        w = WeatherFeatures(temperature=25, wind_speed=10, solar_irradiance=500)
        r = a.predict(w)
        # q50 should be 25*100 = 2500 based on temp being first
        assert r["q50"] == 2500.0

    def test_schema_1_1_uses_ercot_local_calendar_features(self, tmp_path):
        metadata = dict(VALID_METADATA)
        metadata["artifact_schema_version"] = "1.1"
        metadata["feature_names"] = [
            "temperature", "wind_speed", "solar_irradiance",
            "hour", "day_of_week", "month", "is_weekend",
        ]
        metadata["feature_units"] = {
            "temperature": "degC", "wind_speed": "m/s", "solar_irradiance": "W/m2",
            "hour": "local_hour", "day_of_week": "integer_0_monday",
            "month": "integer_1_january", "is_weekend": "binary",
        }
        (tmp_path / "metadata.json").write_text(json.dumps(metadata))
        (tmp_path / "metrics.json").write_text(json.dumps(VALID_METRICS))
        bundle = {key: _SumEstimator() for key in ("q50", "q90", "q95", "q99")}
        (tmp_path / "model.joblib").write_bytes(pickle.dumps(bundle))
        adapter = RealModelAdapter(artifact_dir=str(tmp_path))
        weather = __import__("api.schemas", fromlist=["WeatherFeatures"]).WeatherFeatures(
            temperature=25, wind_speed=10, solar_irradiance=500
        )

        result = adapter.predict(weather, datetime(2025, 1, 1, 6, tzinfo=timezone.utc))

        # 2025-01-01 06:00 UTC = local midnight Wednesday: hour=0, dow=2, month=1.
        assert result["q50"] == 538.0

    def test_schema_1_2_adds_ercot_local_year(self, tmp_path):
        metadata = dict(VALID_METADATA)
        metadata["artifact_schema_version"] = "1.2"
        metadata["feature_names"] = [
            "temperature", "wind_speed", "solar_irradiance",
            "hour", "day_of_week", "month", "is_weekend", "year",
        ]
        metadata["feature_units"] = {
            "temperature": "degC", "wind_speed": "m/s", "solar_irradiance": "W/m2",
            "hour": "local_hour", "day_of_week": "integer_0_monday",
            "month": "integer_1_january", "is_weekend": "binary",
            "year": "ercot_local_year",
        }
        (tmp_path / "metadata.json").write_text(json.dumps(metadata))
        (tmp_path / "metrics.json").write_text(json.dumps(VALID_METRICS))
        bundle = {key: _SumEstimator() for key in ("q50", "q90", "q95", "q99")}
        (tmp_path / "model.joblib").write_bytes(pickle.dumps(bundle))
        adapter = RealModelAdapter(artifact_dir=str(tmp_path))
        weather = __import__("api.schemas", fromlist=["WeatherFeatures"]).WeatherFeatures(
            temperature=25, wind_speed=10, solar_irradiance=500
        )

        result = adapter.predict(weather, datetime(2025, 1, 1, 6, tzinfo=timezone.utc))

        assert result["q50"] == 2563.0

    def test_schema_1_3_requires_server_operational_features(self, tmp_path):
        metadata = dict(VALID_METADATA)
        metadata["artifact_schema_version"] = "1.3"
        metadata["feature_names"] = [
            "temperature", "wind_speed", "solar_irradiance",
            "hour", "day_of_week", "month", "is_weekend", "year",
            "lag_load_1h", "lag_load_24h", "lag_load_168h",
            "rolling_load_mean_24h", "rolling_load_std_24h",
            "rolling_load_mean_168h", "rolling_load_std_168h",
        ]
        metadata["feature_units"] = {
            "temperature": "degC", "wind_speed": "m/s", "solar_irradiance": "W/m2",
            "hour": "local_hour", "day_of_week": "integer_0_monday",
            "month": "integer_1_january", "is_weekend": "binary",
            "year": "ercot_local_year",
            "lag_load_1h": "MW", "lag_load_24h": "MW", "lag_load_168h": "MW",
            "rolling_load_mean_24h": "MW", "rolling_load_std_24h": "MW",
            "rolling_load_mean_168h": "MW", "rolling_load_std_168h": "MW",
        }
        (tmp_path / "metadata.json").write_text(json.dumps(metadata))
        (tmp_path / "metrics.json").write_text(json.dumps(VALID_METRICS))
        bundle = {key: _SumEstimator() for key in ("q50", "q90", "q95", "q99")}
        (tmp_path / "model.joblib").write_bytes(pickle.dumps(bundle))
        adapter = RealModelAdapter(artifact_dir=str(tmp_path))
        weather = __import__("api.schemas", fromlist=["WeatherFeatures"]).WeatherFeatures(
            temperature=25, wind_speed=10, solar_irradiance=500
        )

        with pytest.raises(ModelArtifactError, match="server-supplied"):
            adapter.predict(weather, datetime(2025, 1, 1, 6, tzinfo=timezone.utc))

        operational = {
            "lag_load_1h": 50_000,
            "lag_load_24h": 49_000,
            "lag_load_168h": 48_000,
            "rolling_load_mean_24h": 49_500,
            "rolling_load_std_24h": 1_000,
            "rolling_load_mean_168h": 48_500,
            "rolling_load_std_168h": 1_500,
        }
        result = adapter.predict(
            weather,
            datetime(2025, 1, 1, 6, tzinfo=timezone.utc),
            operational,
        )
        assert result["q50"] == 250_063.0

    def test_get_version_returns_artifact_version(self, object_bundle_dir):
        a = RealModelAdapter(artifact_dir=object_bundle_dir)
        assert a.get_version() == "0.1.0-test"

    def test_supported_region_comes_from_artifact(self, object_bundle_dir):
        adapter = RealModelAdapter(artifact_dir=object_bundle_dir)

        assert adapter.supports_region("ERCOT_NORTH") is True
        assert adapter.supports_region("SPP") is False

    def test_missing_artifact_dir_var(self, monkeypatch):
        monkeypatch.delenv("MODEL_ARTIFACT_DIR", raising=False)
        with pytest.raises(RuntimeError, match="MODEL_ARTIFACT_DIR"):
            RealModelAdapter()

    def test_missing_directory(self):
        with pytest.raises(ModelArtifactError, match="not found"):
            RealModelAdapter(artifact_dir="/tmp/nonexistent_gert_test_dir")

    def test_invalid_artifact(self, tmp_path):
        (tmp_path / "metadata.json").write_text("{}")
        (tmp_path / "metrics.json").write_text("{}")
        (tmp_path / "model.joblib").write_bytes(pickle.dumps("not_a_model"))
        with pytest.raises(ModelArtifactError):
            RealModelAdapter(artifact_dir=str(tmp_path))


class TestFactoryIntegration:
    def test_stub_default(self, monkeypatch):
        monkeypatch.delenv("MODEL_BACKEND", raising=False)
        s = get_model_service()
        assert isinstance(s, QuantileModelStub)

    def test_stub_explicit(self, monkeypatch):
        monkeypatch.setenv("MODEL_BACKEND", "stub")
        s = get_model_service()
        assert isinstance(s, QuantileModelStub)

    def test_real_returns_adapter(self, monkeypatch, object_bundle_dir):
        monkeypatch.setenv("MODEL_BACKEND", "real")
        monkeypatch.setenv("MODEL_ARTIFACT_DIR", object_bundle_dir)
        s = get_model_service()
        assert isinstance(s, RealModelAdapter)
        assert s.get_version() == "0.1.0-test"

    def test_unknown_backend_raises(self, monkeypatch):
        monkeypatch.setenv("MODEL_BACKEND", "typo")
        monkeypatch.delenv("MODEL_ARTIFACT_DIR", raising=False)
        with pytest.raises(RuntimeError, match="Unsupported"):
            get_model_service()


class TestAPI:
    """API integration: MODEL_BACKEND=real with valid artifact."""

    def test_api_predict_with_real_adapter(self, monkeypatch):
        from datetime import datetime
        artifact_path = _build_valid_artifact_dir()
        monkeypatch.setenv("MODEL_BACKEND", "real")
        monkeypatch.setenv("MODEL_ARTIFACT_DIR", artifact_path)
        # Re-import app modules to refresh singletons
        import importlib
        import api.deps
        importlib.reload(api.deps)

        payload = {
            "region": "ERCOT_NORTH",
            "date": datetime.now().isoformat(),
            "weather_features": {
                "temperature": 25.0,
                "wind_speed": 10.0,
                "solar_irradiance": 500.0
            }
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "q99_load_mw" in data
        assert "risk_score" in data
