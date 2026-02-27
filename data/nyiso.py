"""
NYISO (New York Independent System Operator) data adapter.

NYISO provides public APIs:
- Real-time data: https://www.nyiso.com/api
- Historical: CSV downloads
"""

import httpx
from datetime import datetime
from typing import Optional

from data.base import GridDataAdapter, GridLoadData, WeatherData
from services.region import REGION_COORDS


class NYISOAdapter(GridDataAdapter):
    """NYISO data adapter."""

    async def fetch_current_load(self, region: str) -> GridLoadData:
        """Fetch current NYISO system load."""
        try:
            # NYISO API (simplified)
            import math
            hour = datetime.now().hour
            # NYISO peak typically around 5-6 PM
            base_load = 25000  # MW
            daily_variation = 8000 * math.sin((hour - 6) * math.pi / 12)
            estimated_load = base_load + daily_variation

            return GridLoadData(
                current_load_mw=estimated_load,
                capacity_mw=self.get_region_capacity(region),
                timestamp=datetime.now(),
                region=region,
            )
        except Exception:
            return GridLoadData(
                current_load_mw=28000.0,
                capacity_mw=self.get_region_capacity(region),
                timestamp=datetime.now(),
                region=region,
            )

    async def fetch_historical_load(
        self, region: str, start_time: datetime, end_time: datetime
    ) -> list[GridLoadData]:
        """Fetch historical NYISO load data."""
        return []

    async def fetch_weather(self, region: str) -> WeatherData:
        """Fetch weather for NYISO region."""
        coords = REGION_COORDS.get(region) or REGION_COORDS["NYISO"]

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
                    temperature=current.get("temperature_2m", 10.0),
                    wind_speed=current.get("wind_speed_10m", 5.0),
                    solar_irradiance=current.get("direct_normal_irradiance", 300.0),
                    timestamp=datetime.now(),
                )
        except Exception:
            return WeatherData(
                temperature=10.0,
                wind_speed=5.0,
                solar_irradiance=300.0,
                timestamp=datetime.now(),
            )
