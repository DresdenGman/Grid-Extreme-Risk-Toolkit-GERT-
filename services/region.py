from __future__ import annotations

from typing import Dict


# Region Coordinates for Live Weather
REGION_COORDS: Dict[str, Dict[str, float]] = {
    "ERCOT_SYSTEM": {"lat": 31.0, "long": -97.0},  # System context; live weather is multi-point.
    "ERCOT_NORTH": {"lat": 32.7767, "long": -96.7970},  # Dallas, TX
    "CAISO": {"lat": 34.0522, "long": -118.2437},  # Los Angeles, CA
    "PJM": {"lat": 39.9526, "long": -75.1652},  # Philadelphia, PA
    "NYISO": {"lat": 40.7128, "long": -74.0060},  # New York, NY
}

ERCOT_SYSTEM_WEATHER_POINTS = (
    ("NORTH", 32.7767, -96.7970),
    ("SOUTH", 29.4241, -98.4936),
    ("WEST", 31.9973, -102.0779),
    ("HOUSTON", 29.7604, -95.3698),
)

# Fixed from ERCOT zonal load shares in the training period. Recomputed by the
# offline data manifest before model promotion.
ERCOT_SYSTEM_WEATHER_WEIGHTS = {
    "NORTH": 0.3448663984031006,
    "SOUTH": 0.26127382930701115,
    "WEST": 0.1319804768720815,
    "HOUSTON": 0.2618792954178068,
}


def get_region_capacity(region: str) -> float:
    """Returns grid capacity in MW for different ISOs."""
    caps = {
        "ERCOT_SYSTEM": 65000.0,
        "ERCOT_NORTH": 65000.0,
        "CAISO": 50000.0,
        "PJM": 140000.0,
        "NYISO": 32000.0,
    }
    return float(caps.get(region, 55000.0))
