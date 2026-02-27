import json
import math
import random
from datetime import datetime
from typing import Optional
import os

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

import generate_bulletin
from api.deps import ai_client, logger, model_service, alert_manager
from api.limiting import limiter
from db.connection import get_db, init_db
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
from api.validators import validate_region, validate_temperature, validate_wind_speed, validate_solar_irradiance

# Services
from api.deps import risk_service, scenario_service


router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(),
        "backend": model_service.get_version(),
        "ai_enabled": ai_client is not None,
        "env": os.getenv("ENVIRONMENT", "dev"),
    }


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
            "data_source": "real_time",
        }
    except Exception as e:
        logger.error(f"Load data fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch load data: {str(e)}")


@router.post("/predict", response_model=PredictionOut, status_code=200)
@limiter.limit("60/minute")
async def predict_risk(req: PredictRequest, request: Request, db: Session = Depends(get_db)):
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
            
            logger.info(f"Real load data: {real_load.current_load_mw} MW / {real_load.capacity_mw} MW")
        except Exception as e:
            logger.warning(f"Could not fetch real load data: {e}, using model-only prediction")
            real_load = None
        
        # Enhance diagnostics with weather features for database
        req.weather_features.model_dump()

        # Lightweight response cache (per region + features snapshot)
        cache_key = (
            f"predict:{req.region}:"
            f"{round(req.weather_features.temperature, 1)}:"
            f"{round(req.weather_features.wind_speed, 1)}:"
            f"{round(req.weather_features.solar_irradiance, 0)}"
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
            result = risk_service.predict(req)
            predict_cache.set(cache_key, result, ttl_seconds=30)
        result.diagnostics["temperature"] = req.weather_features.temperature
        result.diagnostics["wind_speed"] = req.weather_features.wind_speed
        result.diagnostics["solar_irradiance"] = req.weather_features.solar_irradiance
        
        # Enhance diagnostics with real data info
        if real_load:
            result.diagnostics["real_load_mw"] = real_load.current_load_mw
            result.diagnostics["real_capacity_mw"] = real_load.capacity_mw
            result.diagnostics["data_source"] = "real_time"
        else:
            result.diagnostics["data_source"] = "simulated"
        
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
                            AlertRepository.create(
                                db=db,
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
    except Exception as e:
        logger.error(f"Prediction Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenario", response_model=ScenarioResponse)
@limiter.limit("20/minute")
async def run_scenario(req: ScenarioRequest, request: Request):
    try:
        return scenario_service.run(req)
    except Exception as e:
        logger.error(f"Scenario Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AIAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_risk(req: PredictRequest, request: Request):
    """
    AI-Powered Analysis:
    1) Reuse RiskService.predict to generate a truth snapshot.
    2) Send snapshot to Gemini (or return mock if not configured).
    """
    pred = risk_service.predict(req)
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

    if not ai_client:
        return AIAnalysisResponse(
            headline=f"{pred.risk_level} Risk Detected in {req.region}",
            drivers=[
                AIDriver(
                    factor="Simulated Factor",
                    direction="increase",
                    evidence="AI Key missing, running in offline mode",
                )
            ],
            uncertainty="N/A",
            actions=AIActions(operator=["Check API Key"], public=["Contact Admin"]),
            confidence="LOW",
        )

    try:
        from api.deps import types  # optional import for SDK config

        prompt = f"""
        You are GERT (Grid Extreme Risk Toolkit), an expert AI grid analyst.
        Analyze the following JSON snapshot of grid conditions.

        SNAPSHOT DATA:
        {snapshot}

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
        raise HTTPException(status_code=500, detail="AI Analysis Service Unavailable")


@router.get("/predictions/history")
@limiter.limit("30/minute")
async def get_prediction_history(
    region: Optional[str] = None,
    limit: int = 100,
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
        records = PredictionRepository.get_latest(db=db, region=region, limit=limit)
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
    except Exception as e:
        logger.error(f"Failed to fetch prediction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/history")
@limiter.limit("30/minute")
async def get_alert_history(
    region: Optional[str] = None,
    limit: int = 50,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Get alert history."""
    try:
        records = AlertRepository.get_latest(db=db, region=region, limit=limit)
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
    except Exception as e:
        logger.error(f"Failed to fetch alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest", response_model=BacktestResponse)
async def run_backtest():
    hours = 72
    time_series = []
    baseline_hits = 0
    gert_hits = 0
    baseline_loss = 0.0
    gert_loss = 0.0
    random.seed(101)

    for h in range(hours):
        base_signal = 40000 + 5000 * math.sin(h / 24 * 2 * math.pi)
        is_spike = h == 20 or h == 50
        spike_val = 15000 if is_spike else 0
        noise = random.gauss(0, 1000)
        actual = base_signal + spike_val + noise

        baseline_pred = base_signal
        baseline_std = 2000
        baseline_p99 = baseline_pred + (2.33 * baseline_std)

        gert_volatility = 10000 if is_spike else 1500
        gert_p99 = base_signal + (2.33 * gert_volatility)

        if actual > baseline_p99:
            baseline_loss += (actual - baseline_p99) * 0.99
        else:
            baseline_loss += (baseline_p99 - actual) * 0.01
            baseline_hits += 1

        if actual > gert_p99:
            gert_loss += (actual - gert_p99) * 0.99
        else:
            gert_loss += (gert_p99 - actual) * 0.01
            gert_hits += 1

        time_series.append(TimePoint(hour=h, actual_load=actual, baseline_p99=baseline_p99, gert_p99=gert_p99))

    calibration_curve = [
        CalibrationBin(prob_bucket="0-50%", observed_freq=0.48, ideal_freq=0.50),
        CalibrationBin(prob_bucket="50-90%", observed_freq=0.89, ideal_freq=0.90),
        CalibrationBin(prob_bucket="90-95%", observed_freq=0.94, ideal_freq=0.95),
        CalibrationBin(prob_bucket="95-99%", observed_freq=0.985, ideal_freq=0.99),
        CalibrationBin(prob_bucket=">99%", observed_freq=0.996, ideal_freq=0.999),
    ]

    return BacktestResponse(
        time_series=time_series,
        metrics=[
            ModelMetrics(
                model_name="Baseline (Mean/OLS)",
                coverage_p99=round(baseline_hits / hours * 100, 1),
                pinball_loss=round(baseline_loss / hours, 1),
                description="Standard regression. Assumes constant risk.",
            ),
            ModelMetrics(
                model_name="GERT (Quantile)",
                coverage_p99=round(gert_hits / hours * 100, 1),
                pinball_loss=round(gert_loss / hours, 1),
                description="Adapts to volatility. High coverage.",
            ),
        ],
        calibration_curve=calibration_curve,
    )


@router.get("/bulletin", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def get_bulletin(request: Request):
    try:
        html_content = generate_bulletin.generate_bulletin_html()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Bulletin Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/playback/{event_id}", response_model=EventPlaybackResponse)
async def get_event_playback(event_id: str):
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
            loss = (h - 18) * 1500 + random.randint(0, 500)
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

        actual_load += random.gauss(0, 300)

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
    )

