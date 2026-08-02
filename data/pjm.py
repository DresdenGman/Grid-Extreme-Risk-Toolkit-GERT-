"""
PJM (Pennsylvania-New Jersey-Maryland Interconnection) data adapter.

PJM provides public APIs:
- Real-time data: https://www.pjm.com/api
- Historical: CSV downloads
"""

import httpx
from datetime import datetime
from typing import Optional

from data.base import GridDataAdapter, GridLoadData, WeatherData
from services.region import REGION_COORDS


class PJMAdapter(GridDataAdapter):
    """PJM data adapter."""

    async def fetch_current_load(self, region: str) -> GridLoadData:
        """Fetch current PJM system load."""
        try:
            # PJM API (simplified - real implementation would use PJM API endpoints)
            import math
            hour = datetime.now().hour
            # PJM peak typically around 5-6 PM
            base_load = 100000  # MW (PJM is large)
            daily_variation = 30000 * math.sin((hour - 6) * math.pi / 12)
            estimated_load = base_load + daily_variation

            return GridLoadData(
                current_load_mw=estimated_load,
                capacity_mw=self.get_region_capacity(region),
                timestamp=datetime.now(),
                region=region,
                source="estimated_fallback",
            )
        except Exception:
            return GridLoadData(
                current_load_mw=110000.0,
                capacity_mw=self.get_region_capacity(region),
                timestamp=datetime.now(),
                region=region,
                source="estimated_fallback",
            )

    async def fetch_historical_load(
        self, region: str, start_time: datetime, end_time: datetime
    ) -> list[GridLoadData]:
        """Fetch historical PJM load data."""
        return []

    async def fetch_weather(self, region: str) -> WeatherData:
        """Fetch weather for PJM region."""
        coords = REGION_COORDS.get(region) or REGION_COORDS["PJM"]

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
                    temperature=current.get("temperature_2m", 15.0),
                    wind_speed=current.get("wind_speed_10m", 5.0),
                    solar_irradiance=current.get("direct_normal_irradiance", 400.0),
                    timestamp=datetime.now(),
                    source="official_live",
                )
        except Exception:
            return WeatherData(
                temperature=15.0,
                wind_speed=5.0,
                solar_irradiance=400.0,
                timestamp=datetime.now(),
                source="estimated_fallback",
            )
