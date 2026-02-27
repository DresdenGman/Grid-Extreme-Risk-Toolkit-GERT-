from __future__ import annotations

import random
from typing import Dict

from api.schemas import WeatherFeatures
from features.weather import WeatherFeatureBuilder
from models.interfaces import ModelInterface
from models.quantiles import enforce_quantile_monotonicity


class QuantileModelStub(ModelInterface):
    """
    A deterministic-ish quantile stub to support UI/demo flows.
    Feature engineering is delegated to WeatherFeatureBuilder to keep model code clean/testable.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._feature_builder = WeatherFeatureBuilder()

    def get_version(self) -> str:
        return "stub-v1"

    def predict(self, features: WeatherFeatures) -> Dict[str, float]:
        derived = self._feature_builder.build(features)

        # Keep some variability, but stable for a given temperature + seed.
        random.seed(self.seed + int(features.temperature))
        noise = random.gauss(0, 200)

        q50 = derived.net_load_mean_mw + noise
        q90 = q50 + derived.volatility_base_mw * 1.28
        q95 = q50 + derived.volatility_base_mw * 1.64
        q99 = q50 + derived.volatility_base_mw * 2.33

        return enforce_quantile_monotonicity({"q50": q50, "q90": q90, "q95": q95, "q99": q99})

