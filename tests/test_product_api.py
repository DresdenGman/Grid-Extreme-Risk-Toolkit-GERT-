"""Production-truth and public-surface integration tests."""

from fastapi.testclient import TestClient

from api.app import app
from api.config import config


client = TestClient(app)


def _prediction_payload() -> dict:
    return {
        "region": "ERCOT_SYSTEM",
        "date": "2026-08-30T12:00:00Z",
        "weather_features": {
            "temperature": 31.0,
            "wind_speed": 8.0,
            "solar_irradiance": 650.0,
        },
    }


def test_public_status_reports_capabilities_without_secrets() -> None:
    response = client.get("/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"operational", "degraded"}
    assert payload["model_status"] in {
        "validated_production",
        "provisional_candidate",
        "rejected_candidate",
        "demonstration_stub",
    }
    assert set(payload["capabilities"]) == {
        "official_ercot_data",
        "probabilistic_prediction",
        "scenario_analysis",
        "validated_backtest",
        "presentation_mode",
    }
    serialized = response.text.lower()
    assert "password" not in serialized
    assert "subscription_key" not in serialized


def test_model_evidence_is_public_sanitized_and_rejects_failed_candidate() -> None:
    response = client.get("/model/evidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation_status"] == "rejected_candidate"
    assert payload["all_gates_passed"] is False
    assert payload["observations"] == 96
    assert len(payload["quantile_metrics"]) == 4
    assert any(not gate["passed"] for gate in payload["gates"])
    serialized = response.text.lower()
    assert "password" not in serialized
    assert "subscription_key" not in serialized


def test_production_stub_refuses_prediction(monkeypatch) -> None:
    monkeypatch.setattr(config, "_app_env", "production")

    response = client.post("/predict", json=_prediction_payload())

    assert response.status_code == 503
    assert "validated probabilistic model" in response.json()["detail"].lower()


def test_removed_analysis_endpoint_is_not_exposed() -> None:
    response = client.post("/analyze", json=_prediction_payload())

    assert response.status_code == 404


def test_security_headers_and_request_id_are_applied() -> None:
    response = client.get("/health", headers={"X-Request-ID": "gert-test-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "gert-test-123"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_untrusted_request_id_is_replaced() -> None:
    response = client.get("/health", headers={"X-Request-ID": "bad request id"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] != "bad request id"
    assert len(response.headers["x-request-id"]) == 36


def test_event_reconstruction_is_deterministic_and_labeled() -> None:
    first = client.get("/events/playback/polar-vortex")
    second = client.get("/events/playback/polar-vortex")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["provenance"] == "synthetic_reconstruction"
    assert "not an official ercot event record" in first.json()["methodology_note"].lower()


def test_unknown_event_is_not_fabricated() -> None:
    response = client.get("/events/playback/not-a-real-event")

    assert response.status_code == 404
