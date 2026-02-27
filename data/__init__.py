"""
Data integration layer for real-time grid load and weather data.

This module provides adapters for different ISO (Independent System Operator) APIs:
- ERCOT (Texas)
- CAISO (California)
- PJM (Mid-Atlantic)
- NYISO (New York)

All adapters return unified data structures for consistent model input.
"""

from data.base import GridDataAdapter, GridLoadData, WeatherData
from data.ercot import ERCOTAdapter
from data.caiso import CAISOAdapter
from data.pjm import PJMAdapter
from data.nyiso import NYISOAdapter
from data.factory import get_data_adapter

__all__ = [
    "GridDataAdapter",
    "GridLoadData",
    "WeatherData",
    "ERCOTAdapter",
    "CAISOAdapter",
    "PJMAdapter",
    "NYISOAdapter",
    "get_data_adapter",
]
