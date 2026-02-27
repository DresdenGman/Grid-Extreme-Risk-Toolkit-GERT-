from __future__ import annotations

from dataclasses import dataclass

from api.schemas import WeatherFeatures
from features.base import FeatureBuilder


@dataclass(frozen=True)
class WeatherModelFeatures:
    """
    Derived features used by the quantile stub model.
    Keeping this explicit makes it easy to test and explain model inputs.
    """

    temp_dev_c: float
    base_load_mw: float
    net_load_mean_mw: float
    volatility_base_mw: float


class WeatherFeatureBuilder(FeatureBuilder[WeatherFeatures, WeatherModelFeatures]):
    def build(self, raw: WeatherFeatures) -> WeatherModelFeatures:
        temp_dev = abs(raw.temperature - 20.0)
        base_load = 40000 + (temp_dev**2) * 150
        net_load_mean = base_load - (raw.solar_irradiance * 5)
        volatility_base = 1000 + (raw.wind_speed * 100)
        return WeatherModelFeatures(
            temp_dev_c=temp_dev,
            base_load_mw=base_load,
            net_load_mean_mw=net_load_mean,
            volatility_base_mw=volatility_base,
        )

