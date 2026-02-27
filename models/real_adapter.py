from __future__ import annotations

import logging
from typing import Dict

from api.schemas import WeatherFeatures
from models.interfaces import ModelInterface
from models.quantiles import enforce_quantile_monotonicity

logger = logging.getLogger("gert_backend")


class RealModelAdapter(ModelInterface):
    """
    Placeholder for a real model adapter.
    Still runs quantile monotonicity enforcement to keep post-processing consistent.
    """

    def __init__(self, model_path: str = "models/gert_latest.pkl"):
        self.model_path = model_path
        self._load_model()

    def _load_model(self) -> None:
        logger.info(f"Loading REAL model from {self.model_path}...")
        self.loaded = True

    def get_version(self) -> str:
        return "real-adapter-v2"

    def predict(self, features: WeatherFeatures) -> Dict[str, float]:
        if not getattr(self, "loaded", False):
            raise RuntimeError("Model not loaded")
        base = 42000 + (features.temperature * 100)
        q50 = base
        q90 = base + 2000 + (features.wind_speed * 50)
        q95 = base + 3000 + (features.wind_speed * 80)
        q99 = base + 5000 + (features.wind_speed * 150)
        return enforce_quantile_monotonicity({"q50": q50, "q90": q90, "q95": q95, "q99": q99})

