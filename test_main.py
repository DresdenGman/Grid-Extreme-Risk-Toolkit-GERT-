import pytest
import os
from fastapi.testclient import TestClient
from datetime import datetime
from main import app, QuantileModelStub, RealModelAdapter, WeatherFeatures, get_model_service, assess_risk

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

def test_real_adapter_monotonicity():
    """Ensure real adapter maintains q99 >= q95 >= q90 >= q50"""
    model = RealModelAdapter()
    features = WeatherFeatures(temperature=35, wind_speed=20, solar_irradiance=500)
    res = model.predict(features)
    assert res["q99"] >= res["q95"] >= res["q90"] >= res["q50"]
    # Verify version string
    assert "real" in model.get_version()

def test_risk_logic():
    """Test the standalone business rule engine"""
    # Safe scenario
    lvl, score = assess_risk(40000, capacity=50000)
    assert lvl == "LOW"
    assert score == 0.0 # margin 10000 > 5000 -> score calculation logic
    
    # Dangerous scenario (margin < 0)
    lvl_danger, score_danger = assess_risk(51000, capacity=50000)
    assert lvl_danger == "EXTREME"
    assert score_danger == 100.0

# ==========================
# Integration Tests: Switching
# ==========================

def test_factory_default_stub(monkeypatch):
    """Test that default without env var is Stub"""
    monkeypatch.delenv("MODEL_BACKEND", raising=False)
    service = get_model_service()
    assert isinstance(service, QuantileModelStub)
    assert "stub" in service.get_version()

def test_factory_real_backend(monkeypatch):
    """Test switching to Real backend via env var"""
    monkeypatch.setenv("MODEL_BACKEND", "real")
    service = get_model_service()
    assert isinstance(service, RealModelAdapter)
    assert "real" in service.get_version()

def test_factory_fallback(monkeypatch):
    """Test fallback to stub on unknown backend"""
    monkeypatch.setenv("MODEL_BACKEND", "unknown_nonsense")
    service = get_model_service()
    assert isinstance(service, QuantileModelStub)

# ==========================
# API Integration Tests
# ==========================

def test_api_predict_flow():
    """Test the full API flow"""
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
    assert response.status_code == 200
    data = response.json()
    assert "q99_load_mw" in data
    assert "risk_score" in data
