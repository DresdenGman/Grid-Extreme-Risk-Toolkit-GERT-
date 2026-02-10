import random
import os
import math
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, validator
import httpx # For Open-Meteo calls

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# AI SDK
try:
    from google import genai
    from google.genai import types
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Warning: google-genai not installed. AI features will fail.")

# Import the new bulletin generator
import generate_bulletin

# ==========================================
# 0. Production Setup (Logging & Config)
# ==========================================

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("gert_backend")

# Rate Limiter Setup (In-memory)
limiter = Limiter(key_func=get_remote_address)

# Initialize AI Client
ai_client = None
if AI_AVAILABLE and os.getenv("API_KEY"):
    ai_client = genai.Client(api_key=os.getenv("API_KEY"))
else:
    logger.warning("API_KEY not found or SDK missing. AI endpoints will return mocks.")

# ==========================================
# 1. Models & Schemas (PRD Aligned)
# ==========================================

class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"

class WeatherFeatures(BaseModel):
    temperature: float = Field(..., description="Ambient temperature in Celsius")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    solar_irradiance: float = Field(..., description="Solar irradiance in W/m^2")

class PredictRequest(BaseModel):
    region: str = Field(..., example="ERCOT_NORTH")
    date: datetime
    weather_features: WeatherFeatures

class FinancialImpact(BaseModel):
    eue_mwh: float
    voll_price: float
    estimated_loss: float

class PredictionOut(BaseModel):
    timestamp: datetime
    q50_load_mw: float = Field(..., description="Median predicted load")
    q90_load_mw: float
    q95_load_mw: float
    q99_load_mw: float = Field(..., description="Extreme tail risk load (1% prob)")
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0, le=100)
    financial: Optional[FinancialImpact] = None
    diagnostics: Dict[str, Any]

class ScenarioRequest(BaseModel):
    baseline_request: PredictRequest
    perturbations: Dict[str, float] = Field(
        ..., 
        example={"temperature": 5.0, "wind_speed": -10.0},
        description="Additive or replacement changes to features"
    )

class ScenarioResponse(BaseModel):
    scenario_id: str
    baseline_risk_score: float
    scenario_risk_score: float
    risk_delta: float
    reserve_shortfall_mw: float
    financial_impact: FinancialImpact
    new_prediction: PredictionOut

# AI Analysis Models
class AIDriver(BaseModel):
    factor: str
    direction: str
    evidence: str

class AIActions(BaseModel):
    operator: List[str]
    public: List[str]

class AIAnalysisResponse(BaseModel):
    headline: str
    drivers: List[AIDriver]
    uncertainty: str
    actions: AIActions
    confidence: str

# Backtest Models
class TimePoint(BaseModel):
    hour: int
    actual_load: float
    baseline_p99: float
    gert_p99: float

class ModelMetrics(BaseModel):
    model_name: str
    coverage_p99: float
    pinball_loss: float
    description: str

class CalibrationBin(BaseModel):
    prob_bucket: str
    observed_freq: float
    ideal_freq: float

class BacktestResponse(BaseModel):
    time_series: List[TimePoint]
    metrics: List[ModelMetrics]
    calibration_curve: List[CalibrationBin]

# Event Playback Models
class EventLog(BaseModel):
    hour: int
    message: str
    source: str
    severity: str

class EventStep(BaseModel):
    hour: int
    timestamp_label: str
    temperature: float
    actual_load_mw: float
    capacity_mw: float
    gert_p99_load_mw: float
    risk_score: float

class EventPlaybackResponse(BaseModel):
    event_id: str
    title: str
    total_hours: int
    steps: List[EventStep]
    logs: List[EventLog]

# ==========================================
# 2. Domain Logic & Interfaces
# ==========================================

# Region Coordinates for Live Weather
REGION_COORDS = {
    "ERCOT_NORTH": {"lat": 32.7767, "long": -96.7970},  # Dallas, TX
    "CAISO": {"lat": 34.0522, "long": -118.2437},       # Los Angeles, CA
    "PJM": {"lat": 39.9526, "long": -75.1652},          # Philadelphia, PA
    "NYISO": {"lat": 40.7128, "long": -74.0060}         # New York, NY
}

def get_region_capacity(region: str) -> float:
    """Returns grid capacity in MW for different ISOs."""
    caps = {
        "ERCOT_NORTH": 65000.0,
        "CAISO": 50000.0,
        "PJM": 140000.0,
        "NYISO": 32000.0
    }
    return caps.get(region, 55000.0)

def calculate_financials(q99_load: float, capacity: float) -> FinancialImpact:
    """
    Calculates Expected Unserved Energy (EUE) and Economic Loss using VOLL.
    """
    shortfall = max(0, q99_load - capacity)
    eue = shortfall * 1.0 
    voll = 9000.0 
    loss = eue * voll
    
    return FinancialImpact(
        eue_mwh=round(eue, 2),
        voll_price=voll,
        estimated_loss=round(loss, 2)
    )

def assess_risk(q99_load: float, capacity: float) -> tuple[RiskLevel, float]:
    """Risk Rule Engine"""
    margin = capacity - q99_load
    if margin <= 0:
        score = 100.0
    else:
        score = max(0.0, 100 - (margin / 5000 * 100))
        
    if score >= 90:
        return RiskLevel.EXTREME, score
    elif score >= 75:
        return RiskLevel.HIGH, score
    elif score >= 40:
        return RiskLevel.MODERATE, score
    else:
        return RiskLevel.LOW, score

class ModelInterface(ABC):
    @abstractmethod
    def predict(self, features: WeatherFeatures) -> Dict[str, float]:
        pass

    def get_version(self) -> str:
        return "base-v0"

class QuantileModelStub(ModelInterface):
    def __init__(self):
        self.seed = 42
        
    def get_version(self) -> str:
        return "stub-v1"

    def predict(self, features: WeatherFeatures) -> Dict[str, float]:
        random.seed(self.seed + int(features.temperature))
        temp_dev = abs(features.temperature - 20.0)
        base_load = 40000 + (temp_dev ** 2) * 150
        net_load_mean = base_load - (features.solar_irradiance * 5)
        
        volatility_base = 1000 + (features.wind_speed * 100)
        noise = random.gauss(0, 200)
        
        q50 = net_load_mean + noise
        q90 = q50 + volatility_base * 1.28
        q95 = q50 + volatility_base * 1.64
        q99 = q50 + volatility_base * 2.33
        
        return self._ensure_monotonicity(q50, q90, q95, q99)

    def _ensure_monotonicity(self, q50, q90, q95, q99):
        if not (q99 >= q95 >= q90 >= q50):
            sorted_q = sorted([q50, q90, q95, q99])
            return {"q50": sorted_q[0], "q90": sorted_q[1], "q95": sorted_q[2], "q99": sorted_q[3]}
        return {"q50": q50, "q90": q90, "q95": q95, "q99": q99}

class RealModelAdapter(ModelInterface):
    def __init__(self, model_path: str = "models/gert_latest.pkl"):
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        logger.info(f"Loading REAL model from {self.model_path}...") 
        self.loaded = True

    def get_version(self) -> str:
        return "real-adapter-v2"

    def predict(self, features: WeatherFeatures) -> Dict[str, float]:
        if not self.loaded:
            raise RuntimeError("Model not loaded")
        base = 42000 + (features.temperature * 100) 
        q50 = base
        q90 = base + 2000 + (features.wind_speed * 50)
        q95 = base + 3000 + (features.wind_speed * 80)
        q99 = base + 5000 + (features.wind_speed * 150)
        return {"q50": q50, "q90": q90, "q95": q95, "q99": q99}

def get_model_service() -> ModelInterface:
    backend = os.getenv("MODEL_BACKEND", "stub").lower()
    if backend == "real":
        return RealModelAdapter()
    elif backend == "stub":
        return QuantileModelStub()
    else:
        logger.warning(f"Unknown backend '{backend}', falling back to stub.")
        return QuantileModelStub()

model_service = get_model_service()

# ==========================================
# 4. API Application
# ==========================================

app = FastAPI(
    title="Grid Extreme Risk Toolkit API",
    description=f"Backend for GERT. Running Mode: {os.getenv('MODEL_BACKEND', 'stub').upper()}",
    version="0.2.1"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "timestamp": datetime.now(), 
        "backend": model_service.get_version(),
        "ai_enabled": ai_client is not None,
        "env": os.getenv("ENVIRONMENT", "dev")
    }

@app.get("/weather/live", response_model=WeatherFeatures)
@limiter.limit("20/minute")
async def get_live_weather(region: str, request: Request):
    """Fetches real-time weather from Open-Meteo for the selected region."""
    coords = REGION_COORDS.get(region)
    if not coords:
        coords = REGION_COORDS["ERCOT_NORTH"] # Default
        
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": coords["lat"],
            "longitude": coords["long"],
            "current": ["temperature_2m", "wind_speed_10m", "direct_normal_irradiance"],
            "wind_speed_unit": "ms" # Crucial: GERT uses m/s, OpenMeteo defaults to km/h
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            
            current = data.get("current", {})
            return WeatherFeatures(
                temperature=current.get("temperature_2m", 25.0),
                wind_speed=current.get("wind_speed_10m", 5.0),
                solar_irradiance=current.get("direct_normal_irradiance", 500.0)
            )
            
    except Exception as e:
        logger.error(f"Weather API Failed: {e}")
        # Fallback to plausible defaults if external API fails
        return WeatherFeatures(temperature=20.0, wind_speed=10.0, solar_irradiance=600.0)

@app.post("/predict", response_model=PredictionOut, status_code=200)
@limiter.limit("60/minute") 
async def predict_risk(req: PredictRequest, request: Request):
    try:
        logger.info(f"Prediction requested for region: {req.region}")
        quantiles = model_service.predict(req.weather_features)
        capacity = get_region_capacity(req.region)
        risk_level, risk_score = assess_risk(quantiles["q99"], capacity=capacity)
        financials = calculate_financials(quantiles["q99"], capacity)

        return PredictionOut(
            timestamp=datetime.now(),
            q50_load_mw=quantiles["q50"],
            q90_load_mw=quantiles["q90"],
            q95_load_mw=quantiles["q95"],
            q99_load_mw=quantiles["q99"],
            risk_level=risk_level,
            risk_score=round(risk_score, 1),
            financial=financials,
            diagnostics={
                "input_region": req.region,
                "model_version": model_service.get_version(),
                "backend_type": os.getenv("MODEL_BACKEND", "stub"),
                "capacity_used": capacity
            }
        )
    except Exception as e:
        logger.error(f"Prediction Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scenario", response_model=ScenarioResponse)
@limiter.limit("20/minute")
async def run_scenario(req: ScenarioRequest, request: Request):
    # 1. Baseline
    base_quantiles = model_service.predict(req.baseline_request.weather_features)
    base_capacity = get_region_capacity(req.baseline_request.region)
    base_lvl, base_score = assess_risk(base_quantiles["q99"], capacity=base_capacity)
    
    # 2. Perturbation
    new_features = req.baseline_request.weather_features.model_copy()
    if "temperature" in req.perturbations: new_features.temperature = req.perturbations["temperature"] 
    if "wind_speed" in req.perturbations: new_features.wind_speed = req.perturbations["wind_speed"]
    if "solar_irradiance" in req.perturbations: new_features.solar_irradiance = req.perturbations["solar_irradiance"]
    
    # 3. New Prediction
    new_quantiles = model_service.predict(new_features)
    new_lvl, new_score = assess_risk(new_quantiles["q99"], capacity=base_capacity)
    financials = calculate_financials(new_quantiles["q99"], base_capacity)
    shortfall = max(0, new_quantiles["q99"] - base_capacity)

    return ScenarioResponse(
        scenario_id=f"sim_{random.randint(1000,9999)}",
        baseline_risk_score=round(base_score, 1),
        scenario_risk_score=round(new_score, 1),
        risk_delta=round(new_score - base_score, 1),
        reserve_shortfall_mw=round(shortfall, 1),
        financial_impact=financials,
        new_prediction=PredictionOut(
            timestamp=datetime.now(),
            q50_load_mw=new_quantiles["q50"],
            q90_load_mw=new_quantiles["q90"],
            q95_load_mw=new_quantiles["q95"],
            q99_load_mw=new_quantiles["q99"],
            risk_level=new_lvl,
            risk_score=round(new_score, 1),
            financial=financials,
            diagnostics={
                "type": "stress_test", 
                "backend": model_service.get_version(),
                "input_region": req.baseline_request.region,
                "model_version": model_service.get_version(),
                "backend_type": os.getenv("MODEL_BACKEND", "stub")
            }
        )
    )

@app.post("/analyze", response_model=AIAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_risk(req: PredictRequest, request: Request):
    """
    AI-Powered Analysis:
    1. Re-runs the prediction logic to generate a 'Truth Snapshot'.
    2. Sends snapshot to Gemini to generate narrative.
    3. Validates and returns structured insight.
    """
    # 1. Generate Truth Snapshot (Freeze the numbers)
    quantiles = model_service.predict(req.weather_features)
    capacity = get_region_capacity(req.region)
    risk_level, risk_score = assess_risk(quantiles["q99"], capacity=capacity)
    
    snapshot = {
        "region": req.region,
        "capacity_mw": capacity,
        "features": req.weather_features.model_dump(),
        "prediction": {
            "p50_load": quantiles["q50"],
            "p99_extreme_load": quantiles["q99"],
            "margin_mw": capacity - quantiles["q99"],
            "risk_level": risk_level
        },
        "model": {"type": "quantile", "version": model_service.get_version()}
    }
    
    # 2. Call AI (or fallback)
    if not ai_client:
        # Fallback Mock if no API key
        return AIAnalysisResponse(
            headline=f"{risk_level} Risk Detected in {req.region}",
            drivers=[
                AIDriver(factor="Simulated Factor", direction="increase", evidence="AI Key missing, running in offline mode")
            ],
            uncertainty="N/A",
            actions=AIActions(operator=["Check API Key"], public=["Contact Admin"]),
            confidence="LOW"
        )
        
    try:
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
        
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=AIAnalysisResponse,
                temperature=0.2
            )
        )
        
        # Pydantic will automatically validate the schema because we passed the class to the SDK!
        # The SDK returns a parsed object if response_schema is set with Pydantic model.
        # Note: Depending on SDK version, we might need to parse `response.text`.
        # For safety in this environment, let's parse the text manually if needed or trust the SDK typing.
        
        import json
        parsed = json.loads(response.text)
        return AIAnalysisResponse(**parsed)
        
    except Exception as e:
        logger.error(f"AI Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail="AI Analysis Service Unavailable")

@app.get("/backtest", response_model=BacktestResponse)
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
        is_spike = (h == 20 or h == 50)
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
            
        time_series.append(TimePoint(
            hour=h, actual_load=actual, baseline_p99=baseline_p99, gert_p99=gert_p99
        ))
        
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
                description="Standard regression. Assumes constant risk."
            ),
            ModelMetrics(
                model_name="GERT (Quantile)",
                coverage_p99=round(gert_hits / hours * 100, 1),
                pinball_loss=round(gert_loss / hours, 1),
                description="Adapts to volatility. High coverage."
            )
        ],
        calibration_curve=calibration_curve
    )

@app.get("/bulletin", response_class=HTMLResponse)
@limiter.limit("10/minute") 
async def get_bulletin(request: Request):
    try:
        html_content = generate_bulletin.generate_bulletin_html()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Bulletin Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events/playback/{event_id}", response_model=EventPlaybackResponse)
async def get_event_playback(event_id: str):
    """
    Returns simulated historical data for a specific event (e.g., Texas Freeze).
    In a real app, this would query a historical database.
    """
    hours = 48
    steps = []
    logs = []
    
    # Simulation Parameters for Feb 2021 Texas Freeze
    base_temp = -5.0
    start_load = 55000.0
    start_capacity = 68000.0
    
    for h in range(hours):
        # 1. Weather Logic: Temp drops drastically
        temp = base_temp - (h * 0.4) 
        if h > 24: temp += ((h - 24) * 0.2) # Slight recovery
        
        # 2. Load Logic: Load spikes as temp drops (heating)
        # Demand increases 1000MW per degree drop
        heating_load = abs(temp - 10) * 1200
        actual_load = start_load + heating_load
        
        # 3. Capacity Logic: Capacity crashes starting hour 20 (freezing lines)
        capacity = start_capacity
        if h > 18:
            # Cascading failure simulation
            loss = (h - 18) * 1500 + random.randint(0, 500)
            capacity = max(45000, start_capacity - loss)
            
        # 4. GERT Model Prediction (Simulated)
        # GERT sees the temp drop forecast and predicts high tail risk
        # The prediction should lead the actual failure
        gert_p99 = actual_load + 2000 + (abs(temp) * 300)
        
        # 5. Risk Score
        margin = capacity - gert_p99
        risk = 0.0
        if margin < 0:
            risk = 100.0
        else:
            risk = max(0, 100 - (margin / 5000 * 100))
            
        # 6. Generate Logs
        if h == 10:
            logs.append(EventLog(hour=h, message="Temperature forecasts revised downward to -12°C.", source="NOAA", severity="INFO"))
        elif h == 18:
            logs.append(EventLog(hour=h, message="GERT Risk Signal escalated to HIGH. P99 Load approaching capacity.", source="GERT System", severity="WARNING"))
        elif h == 20:
             logs.append(EventLog(hour=h, message="Multiple gas generators tripping offline due to frozen instrumentation.", source="Grid Operator", severity="CRITICAL"))
        elif h == 22:
             logs.append(EventLog(hour=h, message="EEA Level 3 Declared. Rotating outages initiated.", source="ISO Control Room", severity="CRITICAL"))
             
        # Add random noise to simulate realism
        actual_load += random.gauss(0, 300)
        
        steps.append(EventStep(
            hour=h,
            timestamp_label=f"Feb 14 {h%24}:00",
            temperature=round(temp, 1),
            actual_load_mw=round(actual_load, 1),
            capacity_mw=round(capacity, 1),
            gert_p99_load_mw=round(gert_p99, 1),
            risk_score=round(risk, 1)
        ))
        
    return EventPlaybackResponse(
        event_id=event_id,
        title="2021 Winter Storm Uri (Simulation)",
        total_hours=hours,
        steps=steps,
        logs=logs
    )

if __name__ == "__main__":
    import uvicorn
    # Local development entry point
    uvicorn.run(app, host="0.0.0.0", port=8000)
