from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from domain.types import RiskLevel


class WeatherFeatures(BaseModel):
    temperature: float = Field(..., description="Ambient temperature in Celsius")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    solar_irradiance: float = Field(..., description="Solar irradiance in W/m^2")


class PredictRequest(BaseModel):
    region: str = Field(..., json_schema_extra={"example": "ERCOT_SYSTEM"})
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
        json_schema_extra={"example": {"temperature": 5.0, "wind_speed": -10.0}},
        description="Additive or replacement changes to features",
    )


class ScenarioResponse(BaseModel):
    scenario_id: str
    baseline_risk_score: float
    scenario_risk_score: float
    risk_delta: float
    reserve_shortfall_mw: float
    financial_impact: FinancialImpact
    new_prediction: PredictionOut


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
    provenance: Literal["verified_observation", "synthetic_reconstruction"]
    methodology_note: str


class ProductCapabilities(BaseModel):
    official_ercot_data: bool
    probabilistic_prediction: bool
    scenario_analysis: bool
    validated_backtest: bool
    presentation_mode: bool = True


class ProductStatus(BaseModel):
    status: Literal["operational", "degraded"]
    environment: str
    model_status: Literal[
        "validated_production",
        "provisional_candidate",
        "rejected_candidate",
        "demonstration_stub",
    ]
    model_version: str
    capabilities: ProductCapabilities


class QuantileValidationMetric(BaseModel):
    quantile: Literal["q50", "q90", "q95", "q99"]
    target_coverage: float = Field(..., ge=0, le=1)
    empirical_coverage: float = Field(..., ge=0, le=1)
    absolute_coverage_error: float = Field(..., ge=0, le=1)
    pinball_skill_vs_baseline: float


class ValidationGate(BaseModel):
    gate: str
    passed: bool
    observed: float
    requirement: str


class ModelEvidence(BaseModel):
    candidate_id: str
    validation_status: Literal[
        "validated_production",
        "provisional_candidate",
        "rejected_candidate",
    ]
    summary: str
    evaluation_window_start: str
    evaluation_window_end: str
    observations: int = Field(..., gt=0)
    q50_mae_mw: float = Field(..., ge=0)
    quantile_crossings: int = Field(..., ge=0)
    quantile_metrics: List[QuantileValidationMetric]
    gates: List[ValidationGate]
    all_gates_passed: bool
    data_provenance: str
    limitations: List[str]
    published_at: str
