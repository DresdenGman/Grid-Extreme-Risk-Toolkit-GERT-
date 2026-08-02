"""
ERCOT (Electric Reliability Council of Texas) data adapter.

ERCOT provides public APIs for:
- Real-time load data: https://www.ercot.com/api/data
- Historical data: CSV downloads

Note: ERCOT APIs may require registration for some endpoints.
For demo purposes, we'll use publicly accessible endpoints.
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional

from data.base import GridDataAdapter, GridLoadData, WeatherData
from services.region import REGION_COORDS


class ERCOTAdapter(GridDataAdapter):
    """
    ERCOT data adapter.
    
    ERCOT API endpoints:
    - Real-time load: https://www.ercot.com/api/1/services/read/dashboards/systemWideLoad
    - Load forecast: https://www.ercot.com/api/1/services/read/dashboards/loadForecast
    """

    BASE_URL = "https://www.ercot.com/api/1/services/read/dashboards"

    async def fetch_current_load(self, region: str) -> GridLoadData:
        """
        Fetch current ERCOT system-wide load.
        
        ERCOT doesn't break down by sub-region in public API,
        so we return system-wide load for ERCOT_NORTH.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # ERCOT real-time load endpoint
                url = f"{self.BASE_URL}/systemWideLoad"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                
                # ERCOT API returns nested structure
                # Extract current load (most recent timestamp)
                if isinstance(data, list) and len(data) > 0:
                    latest = data[-1]  # Most recent entry
                    load_mw = float(latest.get("systemWideLoad", 0))
                elif isinstance(data, dict):
                    load_mw = float(data.get("systemWideLoad", 0))
                else:
                    load_mw = 0.0

                if load_mw <= 0:
                    raise ValueError("ERCOT response did not contain a positive system load")

                capacity = self.get_region_capacity(region)
                
                return GridLoadData(
                    current_load_mw=load_mw,
                    capacity_mw=capacity,
                    timestamp=datetime.now(),
                    region=region,
                    source="official_live",
                )
        except Exception as e:
            # Fallback: return estimated load based on time of day
            import math
            hour = datetime.now().hour
            # ERCOT typical daily pattern: peak ~6PM, low ~4AM
            base_load = 45000  # MW
            daily_variation = 15000 * math.sin((hour - 6) * math.pi / 12)
            estimated_load = base_load + daily_variation
            
            return GridLoadData(
                current_load_mw=estimated_load,
                capacity_mw=self.get_region_capacity(region),
                timestamp=datetime.now(),
                region=region,
                source="estimated_fallback",
            )

    async def fetch_historical_load(
        self, region: str, start_time: datetime, end_time: datetime
    ) -> list[GridLoadData]:
        """
        Fetch historical ERCOT load data.
        
        Note: ERCOT provides CSV downloads for historical data.
        For real-time API, we simulate historical by fetching current
        and applying time-based patterns.
        """
        # TODO: Implement CSV parsing or historical API endpoint
        # For now, return empty list (can be extended later)
        return []

    async def fetch_weather(self, region: str) -> WeatherData:
        """
        ERCOT doesn't provide weather data directly.
        Delegate to Open-Meteo using region coordinates.
        """
        coords = REGION_COORDS.get(region)
        if not coords:
            coords = REGION_COORDS["ERCOT_NORTH"]

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
                    temperature=current.get("temperature_2m", 25.0),
                    wind_speed=current.get("wind_speed_10m", 5.0),
                    solar_irradiance=current.get("direct_normal_irradiance", 500.0),
                    timestamp=datetime.now(),
                    source="official_live",
                )
        except Exception:
            # Fallback
            return WeatherData(
                temperature=25.0,
                wind_speed=10.0,
                solar_irradiance=600.0,
                timestamp=datetime.now(),
                source="estimated_fallback",
            )
