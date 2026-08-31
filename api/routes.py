import json
import math
from datetime import datetime
from pathlib import Path
from typing import Optional
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

import generate_bulletin
from api.deps import ai_client, logger, model_service, alert_manager
from api.config import config
from api.limiting import limiter
from db.connection import get_db, get_db_context
from db.repository import PredictionRepository, AlertRepository, GridLoadRepository
from api.schemas import (
    AIAnalysisResponse,
    AIActions,
    AIDriver,
    BacktestResponse,
    CalibrationBin,
    EventLog,
    EventPlaybackResponse,
    EventStep,
    ModelMetrics,
    ModelEvidence,
    ProductCapabilities,
    ProductStatus,
    PredictRequest,
    PredictionOut,
    ScenarioRequest,
    ScenarioResponse,
    TimePoint,
    WeatherFeatures,
)
from risk.scoring import RiskScorer
from services.region import REGION_COORDS
from services.cache import weather_cache, predict_cache
from data.factory import get_data_adapter
from data.base import GridLoadData
from data.ercot import ERCOTAdapter
from models.real_adapter import RealModelAdapter
from api.validators import validate_region, validate_temperature, validate_wind_speed, validate_solar_irradiance

# Services
from api.deps import risk_service, scenario_service


router = APIRouter()

_MODEL_EVIDENCE_PATH = (
    Path(__file__).resolve().parents[1] / "evidence" / "ercot_v1_4_validation.json"
)


def _request_id(request: Request | None) -> str:
    return str(getattr(getattr(request, "state", None), "request_id", "unavailable"))


def _service_failure(message: str, request: Request | None) -> HTTPException:
    return HTTPException(status_code=500, detail=f"{message} Reference: {_request_id(request)}")


def _model_validation_status() -> str:
    if not isinstance(model_service, RealModelAdapter):
        return "demonstration_stub"
    status = model_service.validation_status
    if status in {"validated_production", "provisional_candidate", "rejected_candidate"}:
        return status
    return "provisional_candidate"


def _validated_production_model() -> bool:
    return (
        isinstance(model_service, RealModelAdapter)
        and model_service.validation_status == "validated_production"
    )


async def _operational_model_context(
    req: PredictRequest,
) -> tuple[dict[str, float] | None, datetime | None]:
    """Build server-owned features required by the promoted artifact contract."""
    if not isinstance(model_service, RealModelAdapter):
        return None, None
    if not model_service.requires_operational_features:
        return None, None
    adapter = get_data_adapter(req.region)
    if not isinstance(adapter, ERCOTAdapter):
        raise HTTPException(
            status_code=422,
            detail="The active model requires ERCOT system operational context.",
        )
    try:
        return await adapter.fetch_operational_features(req.date)
    except Exception as exc:
        logger.error("Operational model feature fetch failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Official ERCOT history is unavailable or stale; prediction was not produced.",
        ) from exc


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(),
        "backend": model_service.get_version(),
        "ai_enabled": ai_client is not None,
        "env": config.app_env,
    }


@router.get("/status", response_model=ProductStatus)
async def product_status():
    """Expose public capability state without returning configuration or secrets."""
    validated_model = _validated_production_model()
    official_data = ERCOTAdapter().official_api_configured
    backtest_ready = validated_model and all(
        model_service.get_artifact_file(name).is_file()
        for name in ("backtest_sample.json", "evaluation_report.json")
    )
    return ProductStatus(
        status="operational" if official_data and validated_model else "degraded",
        environment=config.app_env,
        model_status=_model_validation_status(),
        model_version=model_service.get_version(),
        capabilities=ProductCapabilities(
            official_ercot_data=official_data,
            probabilistic_prediction=validated_model,
            scenario_analysis=validated_model,
            validated_backtest=bool(backtest_ready),
            ai_analysis=ai_client is not None and validated_model,
        ),
    )


@router.get("/model/evidence", response_model=ModelEvidence)
@limiter.limit("30/minute")
async def model_evidence(request: Request):
    """Return versioned, sanitized evidence for the latest evaluated candidate."""
    try:
        payload = json.loads(_MODEL_EVIDENCE_PATH.read_text(encoding="utf-8"))
        return ModelEvidence.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.error("Model evidence unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Versioned model evidence is temporarily unavailable.",
        ) from exc


@router.get("/weather/live", response_model=WeatherFeatures)
@limiter.limit("20/minute")
async def get_live_weather(region: str, request: Request):
    """Fetch live weather data for a region."""
    region = validate_region(region)
    try:
        cache_key = f"weather:{region}"
        cached = weather_cache.get(cache_key)
        if cached:
            logger.info(
                "Weather cache hit",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path,
                },
            )
            return cached

        adapter = get_data_adapter(region)
        weather_data = await adapter.fetch_weather(region)
        result = WeatherFeatures(
            temperature=weather_data.temperature,
            wind_speed=weather_data.wind_speed,
            solar_irradiance=weather_data.solar_irradiance,
        )
        weather_cache.set(cache_key, result, ttl_seconds=60)
        return result
    except Exception as e:
        logger.warning(f"Data adapter failed for {region}, falling back to Open-Meteo: {e}")
        # Fallback to direct Open-Meteo call
        coords = REGION_COORDS.get(region) or REGION_COORDS["ERCOT_NORTH"]
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": coords["lat"],
                "longitude": coords["long"],
                "current": ["temperature_2m", "wind_speed_10m", "direct_normal_irradiance"],
                "wind_speed_unit": "ms",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=5.0)
                resp.raise_for_status()
                data = resp.json()
                current = data.get("current", {})
                return WeatherFeatures(
                    temperature=current.get("temperature_2m", 25.0),
                    wind_speed=current.get("wind_speed_10m", 5.0),
                    solar_irradiance=current.get("direct_normal_irradiance", 500.0),
                )
        except Exception as fallback_error:
            logger.error(f"Weather API Failed: {fallback_error}")
            return WeatherFeatures(temperature=20.0, wind_speed=10.0, solar_irradiance=600.0)


@router.get("/load/current")
@limiter.limit("30/minute")
async def get_current_load(region: str, request: Request):
    """Fetch current real-time grid load data for a region."""
    region = validate_region(region)
    try:
        adapter = get_data_adapter(region)
        load_data = await adapter.fetch_current_load(region)
        return {
            "region": region,
            "current_load_mw": load_data.current_load_mw,
            "capacity_mw": load_data.capacity_mw,
            "utilization_percent": (load_data.current_load_mw / load_data.capacity_mw) * 100,
            "timestamp": load_data.timestamp.isoformat() if load_data.timestamp else datetime.now().isoformat(),
            "data_source": load_data.source,
            "capacity_source": load_data.capacity_source,
            "capacity_basis": load_data.capacity_basis,
        }
    except Exception as e:
        logger.error(f"Load data fetch failed: {e}")
        raise _service_failure("Current load service failed.", request) from e


@router.post("/predict", response_model=PredictionOut, status_code=200)
@limiter.limit("60/minute")
async def predict_risk(req: PredictRequest, request: Request, db: Session = Depends(get_db)):
    if config.is_production and not _validated_production_model():
        raise HTTPException(
            status_code=503,
            detail="Validated probabilistic model is not yet available in production.",
        )
    try:
        # Validate inputs
        req.region = validate_region(req.region)
        req.weather_features.temperature = validate_temperature(req.weather_features.temperature)
        req.weather_features.wind_speed = validate_wind_speed(req.weather_features.wind_speed)
        req.weather_features.solar_irradiance = validate_solar_irradiance(req.weather_features.solar_irradiance)
        logger.info(
            f"Prediction requested for region: {req.region}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "path": request.url.path,
            },
        )
        operational_features, feature_origin = await _operational_model_context(req)

        # Try to fetch real load data to enhance prediction
        try:
            adapter = get_data_adapter(req.region)
            real_load = await adapter.fetch_current_load(req.region)
            # Save grid load data to database
            try:
                GridLoadRepository.create(
                    db=db,
                    region=req.region,
                    timestamp=real_load.timestamp or datetime.now(),
                    current_load_mw=real_load.current_load_mw,
                    capacity_mw=real_load.capacity_mw,
                    data_source=req.region.lower().split("_")[0],  # Extract ISO name
                    forecast_load_mw=real_load.forecast_load_mw,
                )
            except Exception as db_error:
                logger.warning(f"Failed to save grid load data: {db_error}")
            
            logger.info(
                "Grid load context: %s MW / %s MW (%s)",
                real_load.current_load_mw,
                real_load.capacity_mw,
                real_load.source,
            )
        except Exception as e:
            logger.warning(f"Could not fetch real load data: {e}, using model-only prediction")
            real_load = None
        
        # Enhance diagnostics with weather features for database
        req.weather_features.model_dump()

        # Lightweight response cache (per region + features snapshot)
        cache_key = (
            f"predict:{req.region}:"
            f"{req.date.strftime('%Y-%m-%dT%H')}:"
            f"{round(req.weather_features.temperature, 1)}:"
            f"{round(req.weather_features.wind_speed, 1)}:"
            f"{round(req.weather_features.solar_irradiance, 0)}:"
            f"{round(real_load.capacity_mw, 0) if real_load else 'configured'}"
        )
        cached_result = predict_cache.get(cache_key)
        if cached_result:
            logger.info(
                "Prediction cache hit",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path,
                },
            )
            result: PredictionOut = cached_result
        else:
            result = risk_service.predict(
                req,
                capacity_mw=(
                    real_load.capacity_mw
                    if real_load and real_load.capacity_source == "official_adequacy"
                    else None
                ),
                operational_features=operational_features,
            )
            predict_cache.set(cache_key, result, ttl_seconds=30)
        result.diagnostics["temperature"] = req.weather_features.temperature
        result.diagnostics["wind_speed"] = req.weather_features.wind_speed
        result.diagnostics["solar_irradiance"] = req.weather_features.solar_irradiance
        if feature_origin is not None:
            result.diagnostics["operational_features_source"] = "official_ercot_history"
            result.diagnostics["operational_features_as_of"] = feature_origin.isoformat()
        
        # Enhance diagnostics with real data info
        if real_load:
            result.diagnostics["real_load_mw"] = real_load.current_load_mw
            result.diagnostics["real_capacity_mw"] = real_load.capacity_mw
            result.diagnostics["load_data_source"] = real_load.source
            result.diagnostics["capacity_data_source"] = real_load.capacity_source
            result.diagnostics["capacity_basis"] = real_load.capacity_basis
        else:
            result.diagnostics["load_data_source"] = "estimated_fallback"
            result.diagnostics["capacity_data_source"] = "configured_reference"
            result.diagnostics["capacity_basis"] = "configured regional reference"
        
        # Save prediction to database
        try:
            PredictionRepository.create(
                db=db,
                prediction=result,
                region=req.region,
                request_date=req.date,
            )
        except Exception as db_error:
            logger.warning(f"Failed to save prediction to database: {db_error}")
        
        # Trigger alert if risk threshold breached (async, non-blocking)
        if alert_manager:
            margin = result.diagnostics.get("capacity_used", 60000) - result.q99_load_mw
            # Fire and forget - don't block response
            try:
                import asyncio
                
                async def send_alert_and_save():
                    alert_results = await alert_manager.send_alert(
                        risk_level=result.risk_level,
                        risk_score=result.risk_score,
                        region=req.region,
                        p99_load=result.q99_load_mw,
                        capacity=result.diagnostics.get("capacity_used", 60000),
                        margin=margin,
                    )
                    # Save alert record
                    if alert_results:
                        try:
                            with get_db_context() as alert_db:
                                AlertRepository.create(
                                    db=alert_db,
                                    region=req.region,
                                    risk_level=result.risk_level.value,
                                    risk_score=result.risk_score,
                                    p99_load=result.q99_load_mw,
                                    capacity=result.diagnostics.get("capacity_used", 60000),
                                    margin=margin,
                                    channels_attempted=list(alert_results.keys()),
                                    channels_successful=[k for k, v in alert_results.items() if v],
                                    reason=f"Risk threshold breached: {result.risk_level.value}",
                                )
                        except Exception as alert_db_error:
                            logger.warning(f"Failed to save alert record: {alert_db_error}")
                
                asyncio.create_task(send_alert_and_save())
            except Exception as e:
                logger.warning(f"Alert scheduling failed: {e}")
            
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Prediction validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction Error: {str(e)}")
        raise _service_failure("Prediction service failed.", request) from e


@router.post("/scenario", response_model=ScenarioResponse)
@limiter.limit("20/minute")
async def run_scenario(req: ScenarioRequest, request: Request):
    if config.is_production and not _validated_production_model():
        raise HTTPException(
            status_code=503,
            detail="Scenario analysis requires a validated production model.",
        )
    try:
        operational_features, _ = await _operational_model_context(req.baseline_request)
        adapter = get_data_adapter(req.baseline_request.region)
        live_context = await adapter.fetch_current_load(req.baseline_request.region)
        capacity_mw = (
            live_context.capacity_mw
            if live_context.capacity_source == "official_adequacy"
            else None
        )
        return scenario_service.run(
            req,
            operational_features=operational_features,
            capacity_mw=capacity_mw,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Scenario Error: {str(e)}")
        raise _service_failure("Scenario service failed.", request) from e


@router.post("/analyze", response_model=AIAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_risk(req: PredictRequest, request: Request):
    """
    AI-Powered Analysis:
    1) Reuse RiskService.predict to generate a truth snapshot.
    2) Send the typed snapshot to Gemini when the optional service is enabled.
    """
    if config.is_production and not _validated_production_model():
        raise HTTPException(
            status_code=503,
            detail="AI analysis requires a validated production model.",
        )
    if not ai_client:
        raise HTTPException(status_code=503, detail="AI analysis is not enabled.")
    try:
        operational_features, _ = await _operational_model_context(req)
        pred = risk_service.predict(req, operational_features=operational_features)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    snapshot = {
        "region": req.region,
        "capacity_mw": pred.diagnostics.get("capacity_used"),
        "features": req.weather_features.model_dump(),
        "prediction": {
            "p50_load": pred.q50_load_mw,
            "p99_extreme_load": pred.q99_load_mw,
            "margin_mw": float(pred.diagnostics.get("capacity_used")) - float(pred.q99_load_mw),
            "risk_level": pred.risk_level,
        },
        "model": {"type": "quantile", "version": pred.diagnostics.get("model_version")},
    }

    try:
        from api.deps import types  # optional import for SDK config

        prompt = f"""
        You are GERT (Grid Extreme Risk Toolkit), an expert AI grid analyst.
        Analyze the following JSON snapshot of grid conditions.

        SNAPSHOT DATA:
        {json.dumps(snapshot, default=str, sort_keys=True)}

        INSTRUCTIONS:
        1. Headline: Summarize the risk situation in one punchy sentence.
        2. Drivers: Identify top 2 factors (weather/load) driving the P99 load. MUST reference specific numbers from snapshot 'evidence'.
        3. Uncertainty: Explain why P99 is higher than P50 (e.g. wind volatility).
        4. Actions: Recommend specific actions for Grid Operators and the Public based on the Risk Level.

        CONSTRAINTS:
        - Do not hallucinate capacity or weather values not in the snapshot.
        - Strict JSON output matching the schema.
        """

        response = ai_client.models.generate_content(  # type: ignore[union-attr]
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(  # type: ignore[union-attr]
                response_mime_type="application/json",
                response_schema=AIAnalysisResponse,
                temperature=0.2,
            ),
        )
        parsed = json.loads(response.text)
        return AIAnalysisResponse(**parsed)
    except Exception as e:
        logger.error(f"AI Analysis Failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"AI analysis service is unavailable. Reference: {_request_id(request)}",
        ) from e


@router.get("/predictions/history")
@limiter.limit("30/minute")
async def get_prediction_history(
    region: Optional[str] = None,
    limit: int = Query(100, ge=1, le=200),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    Get prediction history.
    
    Args:
        region: Optional region filter
        limit: Maximum number of records to return
    """
    try:
        validated_region = validate_region(region) if region else None
        records = PredictionRepository.get_latest(db=db, region=validated_region, limit=limit)
        return {
            "count": len(records),
            "predictions": [
                {
                    "id": r.id,
                    "region": r.region,
                    "timestamp": r.timestamp.isoformat(),
                    "risk_level": r.risk_level,
                    "risk_score": r.risk_score,
                    "q99_load_mw": r.q99_load_mw,
                    "capacity_mw": r.capacity_mw,
                    "margin_mw": r.margin_mw,
                    "data_source": r.data_source,
                }
                for r in records
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch prediction history: {e}")
        raise _service_failure("Prediction history service failed.", request) from e


@router.get("/alerts/history")
@limiter.limit("30/minute")
async def get_alert_history(
    region: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get alert history."""
    try:
        validated_region = validate_region(region) if region else None
        records = AlertRepository.get_latest(db=db, region=validated_region, limit=limit)
        return {
            "count": len(records),
            "alerts": [
                {
                    "id": r.id,
                    "region": r.region,
                    "timestamp": r.timestamp.isoformat(),
                    "risk_level": r.risk_level,
                    "risk_score": r.risk_score,
                    "channels_successful": r.channels_successful,
                    "reason": r.reason,
                }
                for r in records
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch alert history: {e}")
        raise _service_failure("Alert history service failed.", request) from e


@router.get("/backtest", response_model=BacktestResponse)
@limiter.limit("20/minute")
async def run_backtest(request: Request):
    from models.real_adapter import RealModelAdapter

    if not _validated_production_model():
        raise HTTPException(
            status_code=503,
            detail="Validated backtest unavailable until a production-validated artifact is active",
        )
    sample_path = model_service.get_artifact_file("backtest_sample.json")
    report_path = model_service.get_artifact_file("evaluation_report.json")
    if not sample_path.is_file() or not report_path.is_file():
        raise HTTPException(status_code=503, detail="Real model artifact does not include validated backtest evidence")
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    model = report["model"]
    baseline = report["baseline"]
    return BacktestResponse(
        time_series=[
            TimePoint(
                hour=int(row["hour"]),
                actual_load=float(row["actual_load"]),
                baseline_p99=float(row["baseline_p99"]),
                gert_p99=float(row["gert_p99"]),
            )
            for row in sample
        ],
        metrics=[
            ModelMetrics(
                model_name="Month-hour climatology",
                coverage_p99=round(float(baseline["empirical_coverage"]["q99"]) * 100, 2),
                pinball_loss=round(float(baseline["pinball_loss"]["q99"]), 2),
                description="2025 holdout baseline derived from 2019-2024 only.",
            ),
            ModelMetrics(
                model_name=model_service.get_version(),
                coverage_p99=round(float(model["empirical_coverage"]["q99"]) * 100, 2),
                pinball_loss=round(float(model["pinball_loss"]["q99"]), 2),
                description="Observed 2025 holdout performance; not simulated.",
            ),
        ],
        calibration_curve=[
            CalibrationBin(
                prob_bucket=key.upper(),
                observed_freq=float(model["empirical_coverage"][key]),
                ideal_freq=quantile,
            )
            for key, quantile in (("q50", 0.5), ("q90", 0.9), ("q95", 0.95), ("q99", 0.99))
        ],
    )


@router.get("/bulletin", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def get_bulletin(request: Request):
    try:
        html_content = generate_bulletin.generate_bulletin_html()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Bulletin Generation Error: {e}")
        raise _service_failure("Bulletin service failed.", request) from e


@router.get("/events/playback/{event_id}", response_model=EventPlaybackResponse)
async def get_event_playback(event_id: str):
    if event_id not in {"polar-vortex", "ercot-2021-presentation"}:
        raise HTTPException(status_code=404, detail="Event reconstruction not found.")
    hours = 48
    steps = []
    logs = []
    scorer = RiskScorer()

    base_temp = -5.0
    start_load = 55000.0
    start_capacity = 68000.0

    for h in range(hours):
        temp = base_temp - (h * 0.4)
        if h > 24:
            temp += (h - 24) * 0.2

        heating_load = abs(temp - 10) * 1200
        actual_load = start_load + heating_load

        capacity = start_capacity
        if h > 18:
            loss = (h - 18) * 1500 + 250 * (1 + math.sin(h * 1.7))
            capacity = max(45000, start_capacity - loss)

        gert_p99 = actual_load + 2000 + (abs(temp) * 300)
        risk = scorer.score(p99_load_mw=gert_p99, capacity_mw=capacity)

        if h == 10:
            logs.append(EventLog(hour=h, message="Temperature forecasts revised downward to -12°C.", source="NOAA", severity="INFO"))
        elif h == 18:
            logs.append(
                EventLog(
                    hour=h,
                    message="GERT Risk Signal escalated to HIGH. P99 Load approaching capacity.",
                    source="GERT System",
                    severity="WARNING",
                )
            )
        elif h == 20:
            logs.append(
                EventLog(
                    hour=h,
                    message="Multiple gas generators tripping offline due to frozen instrumentation.",
                    source="Grid Operator",
                    severity="CRITICAL",
                )
            )
        elif h == 22:
            logs.append(
                EventLog(
                    hour=h,
                    message="EEA Level 3 Declared. Rotating outages initiated.",
                    source="ISO Control Room",
                    severity="CRITICAL",
                )
            )

        actual_load += 180 * math.sin(h * 0.83)

        steps.append(
            EventStep(
                hour=h,
                timestamp_label=f"Feb 14 {h%24}:00",
                temperature=round(temp, 1),
                actual_load_mw=round(actual_load, 1),
                capacity_mw=round(capacity, 1),
                gert_p99_load_mw=round(gert_p99, 1),
                risk_score=round(risk.score, 1),
            )
        )

    return EventPlaybackResponse(
        event_id=event_id,
        title="2021 Winter Storm Uri (Simulation)",
        total_hours=hours,
        steps=steps,
        logs=logs,
        provenance="synthetic_reconstruction",
        methodology_note=(
            "Deterministic educational reconstruction. Values are not an official ERCOT "
            "event record and are not evidence of historical GERT performance."
        ),
    )
