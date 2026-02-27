"""
Model adapter that uses real grid load data to improve predictions.

This adapter combines:
1. Real-time load data from ISO APIs
2. Weather features
3. Historical patterns

To produce more accurate quantile predictions.
"""

from typing import Dict, Optional

from api.schemas import WeatherFeatures
from data.base import GridLoadData
from features.weather import WeatherFeatureBuilder
from models.interfaces import ModelInterface
from models.quantiles import enforce_quantile_monotonicity


class RealDataModelAdapter(ModelInterface):
    """
    Model adapter that leverages real grid load data.
    
    When real load data is available, it:
    1. Uses current load as a baseline
    2. Applies weather-driven adjustments
    3. Adds uncertainty based on historical volatility
    """

    def __init__(self):
        self._feature_builder = WeatherFeatureBuilder()

    def get_version(self) -> str:
        return "real-data-v1"

    def predict(
        self,
        features: WeatherFeatures,
        real_load: Optional[GridLoadData] = None,
    ) -> Dict[str, float]:
        """
        Predict quantiles using real data when available.
        
        Args:
            features: Weather features
            real_load: Optional real-time load data
            
        Returns:
            Dict with q50, q90, q95, q99 quantiles
        """
        derived = self._feature_builder.build(features)

        if real_load:
            # Use real load as baseline
            base_q50 = real_load.current_load_mw
            
            # Apply weather-driven adjustments
            # Temperature effect: ~100 MW per degree deviation from 20°C
            temp_effect = (features.temperature - 20.0) * 100
            
            # Wind effect: negative correlation (more wind = more renewables = less net load)
            wind_effect = -features.wind_speed * 50
            
            # Solar effect: negative correlation
            solar_effect = -features.solar_irradiance * 0.5
            
            adjusted_q50 = base_q50 + temp_effect + wind_effect + solar_effect
            
            # Volatility based on:
            # 1. Weather volatility (from feature builder)
            # 2. Current utilization (high utilization = higher uncertainty)
            utilization = real_load.current_load_mw / real_load.capacity_mw
            utilization_multiplier = 1.0 + (utilization - 0.7) * 0.5  # Higher uncertainty when >70% utilized
            
            volatility = derived.volatility_base_mw * utilization_multiplier
        else:
            # Fallback to feature-based prediction
            adjusted_q50 = derived.net_load_mean_mw
            volatility = derived.volatility_base_mw

        # Generate quantiles
        q50 = adjusted_q50
        q90 = q50 + volatility * 1.28
        q95 = q50 + volatility * 1.64
        q99 = q50 + volatility * 2.33

        return enforce_quantile_monotonicity(
            {"q50": q50, "q90": q90, "q95": q95, "q99": q99}
        )
