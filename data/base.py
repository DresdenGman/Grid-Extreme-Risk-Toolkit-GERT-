"""
Base classes and data models for grid data adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WeatherData:
    """Unified weather data structure."""
    temperature: float  # Celsius
    wind_speed: float  # m/s
    solar_irradiance: float  # W/m^2
    humidity: Optional[float] = None  # 0-100%
    timestamp: Optional[datetime] = None


@dataclass
class GridLoadData:
    """Unified grid load data structure."""
    current_load_mw: float
    capacity_mw: float
    forecast_load_mw: Optional[float] = None  # Next hour forecast
    timestamp: Optional[datetime] = None
    region: Optional[str] = None


class GridDataAdapter(ABC):
    """
    Abstract base class for ISO-specific data adapters.
    
    Each ISO (ERCOT, CAISO, etc.) has different API formats.
    Adapters normalize them into unified structures.
    """

    @abstractmethod
    async def fetch_current_load(self, region: str) -> GridLoadData:
        """
        Fetch current grid load data for a region.
        
        Args:
            region: ISO region identifier (e.g., "ERCOT_NORTH")
            
        Returns:
            GridLoadData with current load, capacity, and timestamp
        """
        pass

    @abstractmethod
    async def fetch_historical_load(
        self, region: str, start_time: datetime, end_time: datetime
    ) -> list[GridLoadData]:
        """
        Fetch historical load data for analysis/backtesting.
        
        Args:
            region: ISO region identifier
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of GridLoadData points
        """
        pass

    @abstractmethod
    async def fetch_weather(self, region: str) -> WeatherData:
        """
        Fetch current weather data for a region.
        
        Note: Some ISOs provide weather, others require external APIs.
        This method may delegate to Open-Meteo or similar.
        
        Args:
            region: ISO region identifier
            
        Returns:
            WeatherData with temperature, wind, solar irradiance
        """
        pass

    def get_region_capacity(self, region: str) -> float:
        """
        Get installed capacity for a region (MW).
        
        This is usually static configuration, but some ISOs provide it via API.
        """
        from services.region import get_region_capacity
        return get_region_capacity(region)
