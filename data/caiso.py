"""
CAISO (California Independent System Operator) data adapter.

CAISO provides public APIs:
- OASIS (Open Access Same-Time Information System)
- Real-time load: https://www.caiso.com/Pages/default.aspx

Note: Some endpoints may require registration.
"""

import httpx
from datetime import datetime
from typing import Optional

from data.base import GridDataAdapter, GridLoadData, WeatherData
from services.region import REGION_COORDS


class CAISOAdapter(GridDataAdapter):
    """
    CAISO data adapter.
    
    CAISO OASIS endpoints:
    - Real-time load: Various OASIS queries
    - Historical: CSV exports available
    """

    async def fetch_current_load(self, region: str) -> GridLoadData:
        """
        Fetch current CAISO system load.
        
        CAISO APIs are more complex and may require OASIS queries.
        For demo, we'll use a simplified approach with fallback.
        """
        try:
            # CAISO OASIS API (simplified - real implementation would use OASIS queries)
            # For now, use estimated load based on time
            import math
            hour = datetime.now().hour
            # CAISO peak typically around 6-7 PM
            base_load = 30000  # MW
            daily_variation = 10000 * math.sin((hour - 7) * math.pi / 12)
            estimated_load = base_load + daily_variation

            return GridLoadData(
                current_load_mw=estimated_load,
                capacity_mw=self.get_region_capacity(region),
                timestamp=datetime.now(),
                region=region,
            )
        except Exception:
            # Fallback
            return GridLoadData(
                current_load_mw=35000.0,
                capacity_mw=self.get_region_capacity(region),
                timestamp=datetime.now(),
                region=region,
            )

    async def fetch_historical_load(
        self, region: str, start_time: datetime, end_time: datetime
    ) -> list[GridLoadData]:
        """Fetch historical CAISO load data."""
        # TODO: Implement CAISO historical data parsing
        return []

    async def fetch_weather(self, region: str) -> WeatherData:
        """Fetch weather for CAISO region via Open-Meteo."""
        coords = REGION_COORDS.get(region) or REGION_COORDS["CAISO"]

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": coords["lat"],
                    "longitude": coords["long"],
                    "current": [
                        "temperature_2m",
                        "wind_speed_10m",
                        "direct_normal_irradiance",
                    ],
                    "wind_speed_unit": "ms",
                }
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                current = data.get("current", {})

                return WeatherData(
                    temperature=current.get("temperature_2m", 20.0),
                    wind_speed=current.get("wind_speed_10m", 5.0),
                    solar_irradiance=current.get("direct_normal_irradiance", 800.0),
                    timestamp=datetime.now(),
                )
        except Exception:
            return WeatherData(
                temperature=20.0,
                wind_speed=5.0,
                solar_irradiance=800.0,
                timestamp=datetime.now(),
            )
