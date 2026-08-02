import pytest
import os
from fastapi.testclient import TestClient
from datetime import datetime
from api.app import app
from api.schemas import WeatherFeatures, PredictRequest
from domain.types import RiskLevel
from features.weather import WeatherFeatureBuilder
from models.factory import get_model_service
from models.quantiles import enforce_quantile_monotonicity
from models.stub import QuantileModelStub
from risk.scoring import RiskScorer
from bulletin.context import build_bulletin_context
from services.scenario_service import ScenarioComparator
from services.region import get_region_capacity

client = TestClient(app)

# ==========================
# Unit Tests: Model Logic
# ==========================

def test_stub_monotonicity():
    """Ensure stub maintains q99 >= q95 >= q90 >= q50"""
    model = QuantileModelStub()
    features = WeatherFeatures(temperature=35, wind_speed=20, solar_irradiance=500)
    res = model.predict(features)
    assert res["q99"] >= res["q95"] >= res["q90"] >= res["q50"]


def test_risk_logic():
    """Test the decision rule engine boundaries (business rule)"""
    scorer = RiskScorer()

    # Safe scenario (large margin -> LOW and 0)
    res = scorer.score(p99_load_mw=40000, capacity_mw=50000)
    assert res.level == RiskLevel.LOW
    assert res.score == 0.0

    # Dangerous scenario (margin <= 0 -> EXTREME and 100)
    res_danger = scorer.score(p99_load_mw=51000, capacity_mw=50000)
    assert res_danger.level == RiskLevel.EXTREME
    assert res_danger.score == 100.0

    # Boundary checks
    # score = 90 -> EXTREME
    res90 = scorer.score(p99_load_mw=49500, capacity_mw=50000)  # margin=500 => 90
    assert res90.level == RiskLevel.EXTREME
    # score = 75 -> HIGH
    res75 = scorer.score(p99_load_mw=48750, capacity_mw=50000)  # margin=1250 => 75
    assert res75.level == RiskLevel.HIGH
    # score = 40 -> MODERATE
    res40 = scorer.score(p99_load_mw=47000, capacity_mw=50000)  # margin=3000 => 40
    assert res40.level == RiskLevel.MODERATE

# ==========================
# Unit Tests: Feature & Quantile utilities
# ==========================

def test_feature_engineering_extreme_temp_amplifies_base_load():
    builder = WeatherFeatureBuilder()
    mild = WeatherFeatures(temperature=20, wind_speed=5, solar_irradiance=500)
    extreme = WeatherFeatures(temperature=35, wind_speed=5, solar_irradiance=500)
    mild_f = builder.build(mild)
    extreme_f = builder.build(extreme)
    assert extreme_f.base_load_mw > mild_f.base_load_mw


def test_quantile_monotonicity_enforcement():
    fixed = enforce_quantile_monotonicity({"q50": 10, "q90": 5, "q95": 9, "q99": 7})
    assert fixed["q99"] >= fixed["q95"] >= fixed["q90"] >= fixed["q50"]


def test_scenario_comparator_delta_and_shortfall():
    comp = ScenarioComparator()
    capacity = get_region_capacity("ERCOT_NORTH")
    baseline = {
        "timestamp": datetime.now().isoformat(),
        "q50_load_mw": 40000,
        "q90_load_mw": 42000,
        "q95_load_mw": 43000,
        "q99_load_mw": 44000,
        "risk_level": "LOW",
        "risk_score": 10.0,
        "financial": None,
        "diagnostics": {"capacity_used": capacity},
    }
    scenario = dict(baseline)
    scenario["risk_score"] = 55.5
    scenario["q99_load_mw"] = capacity + 1000

    from api.schemas import PredictionOut
    b = PredictionOut(**baseline)
    s = PredictionOut(**scenario)
    out = comp.compare(b, s, capacity_mw=capacity)
    assert out.risk_delta == round(55.5 - 10.0, 1)
    assert out.reserve_shortfall_mw == 1000.0


def test_bulletin_context_has_required_fields():
    ctx = build_bulletin_context()
    for k in ["issued_at", "hours", "p50", "p99", "capacity", "risk_level", "max_risk_score", "risk_color", "templates"]:
        assert k in ctx

# ==========================
# Integration Tests: Backend Switching
# ==========================

def test_factory_default_stub(monkeypatch):
    """Test that unset MODEL_BACKEND returns Stub."""
    monkeypatch.delenv("MODEL_BACKEND", raising=False)
    service = get_model_service()
    assert isinstance(service, QuantileModelStub)


def test_factory_stub_explicit(monkeypatch):
    """Test that MODEL_BACKEND=stub returns Stub."""
    monkeypatch.setenv("MODEL_BACKEND", "stub")
    service = get_model_service()
    assert isinstance(service, QuantileModelStub)


def test_factory_real_missing_dir_raises(monkeypatch):
    """Test that MODEL_BACKEND=real without MODEL_ARTIFACT_DIR raises explicit error."""
    monkeypatch.setenv("MODEL_BACKEND", "real")
    monkeypatch.delenv("MODEL_ARTIFACT_DIR", raising=False)
    with pytest.raises(RuntimeError) as exc_info:
        get_model_service()
    assert "MODEL_ARTIFACT_DIR" in str(exc_info.value)


def test_factory_unknown_raises(monkeypatch):
    """Test that unknown backend raises configuration error."""
    monkeypatch.setenv("MODEL_BACKEND", "typo_backend")
    with pytest.raises(RuntimeError) as exc_info:
        get_model_service()
    assert "Unsupported" in str(exc_info.value)

# ==========================
# API Integration Tests
# ==========================

def test_api_predict_flow():
    """Test the full API flow with valid region."""
    payload = {
        "region": "ERCOT_NORTH",
        "date": datetime.now().isoformat(),
        "weather_features": {
            "temperature": 30.0,
            "wind_speed": 10.0,
            "solar_irradiance": 800.0
        }
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "q99_load_mw" in data
    assert "risk_score" in data
    assert data["diagnostics"]["backend_type"] == "stub"
    assert data["diagnostics"]["load_data_source"] in {
        "official_live",
        "estimated_fallback",
    }


def test_health_reports_app_env():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["env"] in {"development", "test", "production"}


def test_api_predict_rejects_invalid_region():
    """Test that invalid region returns 422 with supported regions listed."""
    payload = {
        "region": "TEST_REGION",
        "date": datetime.now().isoformat(),
        "weather_features": {
            "temperature": 30.0,
            "wind_speed": 10.0,
            "solar_irradiance": 800.0
        }
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "TEST_REGION" in str(data)
    assert "ERCOT_NORTH" in str(data)
