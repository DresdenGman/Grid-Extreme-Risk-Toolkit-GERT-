from __future__ import annotations

from typing import Dict


# Region Coordinates for Live Weather
REGION_COORDS: Dict[str, Dict[str, float]] = {
    "ERCOT_NORTH": {"lat": 32.7767, "long": -96.7970},  # Dallas, TX
    "CAISO": {"lat": 34.0522, "long": -118.2437},  # Los Angeles, CA
    "PJM": {"lat": 39.9526, "long": -75.1652},  # Philadelphia, PA
    "NYISO": {"lat": 40.7128, "long": -74.0060},  # New York, NY
}


def get_region_capacity(region: str) -> float:
    """Returns grid capacity in MW for different ISOs."""
    caps = {
        "ERCOT_NORTH": 65000.0,
        "CAISO": 50000.0,
        "PJM": 140000.0,
        "NYISO": 32000.0,
    }
    return float(caps.get(region, 55000.0))

