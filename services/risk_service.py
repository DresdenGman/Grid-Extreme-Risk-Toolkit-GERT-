from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from api.schemas import PredictRequest, PredictionOut, WeatherFeatures
from models.interfaces import ModelInterface
from models.quantiles import enforce_quantile_monotonicity
from risk.financials import calculate_financials
from risk.scoring import RiskScorer
from services.region import get_region_capacity


@dataclass(frozen=True)
class QuantilePrediction:
    q50: float
    q90: float
    q95: float
    q99: float


class RiskService:
    """
    Orchestrates the prediction flow:
    - features (already validated by Pydantic)
    - model predict
    - quantile post-processing (monotonicity)
    - risk scoring (business rule)
    - financial impact (business rule)
    """

    def __init__(self, model: ModelInterface, scorer: RiskScorer | None = None):
        self.model = model
        self.scorer = scorer or RiskScorer()

    def predict(self, req: PredictRequest, capacity_mw: float | None = None) -> PredictionOut:
        capacity = capacity_mw if capacity_mw is not None else get_region_capacity(req.region)
        quantiles = self._predict_quantiles(req.weather_features)

        risk = self.scorer.score(p99_load_mw=quantiles.q99, capacity_mw=capacity)
        financials = calculate_financials(p99_load_mw=quantiles.q99, capacity_mw=capacity)

        return PredictionOut(
            timestamp=datetime.now(),
            q50_load_mw=quantiles.q50,
            q90_load_mw=quantiles.q90,
            q95_load_mw=quantiles.q95,
            q99_load_mw=quantiles.q99,
            risk_level=risk.level,
            risk_score=round(risk.score, 1),
            financial=financials,
            diagnostics={
                "input_region": req.region,
                "model_version": self.model.get_version(),
                "backend_type": os.getenv("MODEL_BACKEND", "stub"),
                "capacity_used": capacity,
            },
        )

    def _predict_quantiles(self, features: WeatherFeatures) -> QuantilePrediction:
        raw: Dict[str, float] = self.model.predict(features)
        fixed = enforce_quantile_monotonicity(raw)
        return QuantilePrediction(
            q50=float(fixed["q50"]),
            q90=float(fixed["q90"]),
            q95=float(fixed["q95"]),
            q99=float(fixed["q99"]),
        )
