from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Mapping

from api.schemas import PredictionOut, ScenarioRequest, ScenarioResponse, WeatherFeatures
from risk.financials import calculate_financials
from services.region import get_region_capacity
from services.risk_service import RiskService


@dataclass(frozen=True)
class ScenarioComparison:
    baseline_risk_score: float
    scenario_risk_score: float
    risk_delta: float
    reserve_shortfall_mw: float


class ScenarioComparator:
    def compare(self, baseline: PredictionOut, scenario: PredictionOut, capacity_mw: float) -> ScenarioComparison:
        baseline_score = float(baseline.risk_score)
        scenario_score = float(scenario.risk_score)
        reserve_shortfall = max(0.0, float(scenario.q99_load_mw) - float(capacity_mw))
        return ScenarioComparison(
            baseline_risk_score=baseline_score,
            scenario_risk_score=scenario_score,
            risk_delta=round(scenario_score - baseline_score, 1),
            reserve_shortfall_mw=round(reserve_shortfall, 1),
        )


class ScenarioService:
    def __init__(self, risk_service: RiskService, comparator: ScenarioComparator | None = None):
        self.risk_service = risk_service
        self.comparator = comparator or ScenarioComparator()

    def run(
        self,
        req: ScenarioRequest,
        operational_features: Mapping[str, float] | None = None,
        capacity_mw: float | None = None,
    ) -> ScenarioResponse:
        # 1) Baseline: reuse the same prediction service (no duplicated logic).
        baseline_pred = self.risk_service.predict(
            req.baseline_request,
            capacity_mw=capacity_mw,
            operational_features=operational_features,
        )
        capacity = capacity_mw or get_region_capacity(req.baseline_request.region)

        # 2) Perturbations: apply deltas/replacements to features.
        new_features = self._apply_perturbations(req.baseline_request.weather_features, req.perturbations)
        new_req = req.baseline_request.model_copy(update={"weather_features": new_features})

        # 3) Scenario prediction (same flow).
        scenario_pred = self.risk_service.predict(
            new_req,
            capacity_mw=capacity_mw,
            operational_features=operational_features,
        )

        # 4) Compare + financial impact.
        comp = self.comparator.compare(baseline_pred, scenario_pred, capacity_mw=capacity)
        financials = calculate_financials(p99_load_mw=float(scenario_pred.q99_load_mw), capacity_mw=capacity)

        return ScenarioResponse(
            scenario_id=f"sim_{random.randint(1000, 9999)}",
            baseline_risk_score=round(comp.baseline_risk_score, 1),
            scenario_risk_score=round(comp.scenario_risk_score, 1),
            risk_delta=comp.risk_delta,
            reserve_shortfall_mw=comp.reserve_shortfall_mw,
            financial_impact=financials,
            new_prediction=scenario_pred,
        )

    def _apply_perturbations(self, base: WeatherFeatures, perturbations: dict[str, float]) -> WeatherFeatures:
        updated = base.model_copy()
        if "temperature" in perturbations:
            updated.temperature = perturbations["temperature"]
        if "wind_speed" in perturbations:
            updated.wind_speed = perturbations["wind_speed"]
        if "solar_irradiance" in perturbations:
            updated.solar_irradiance = perturbations["solar_irradiance"]
        return updated
