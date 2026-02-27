"""
API input validators for request validation.
"""

from typing import List
from fastapi import HTTPException

# Supported regions
VALID_REGIONS = [
    "ERCOT_NORTH",
    "CAISO",
    "PJM",
    "NYISO",
]

# Valid parameter ranges
TEMPERATURE_MIN = -50.0
TEMPERATURE_MAX = 60.0
WIND_SPEED_MIN = 0.0
WIND_SPEED_MAX = 100.0
SOLAR_IRRADIANCE_MIN = 0.0
SOLAR_IRRADIANCE_MAX = 1500.0


def validate_region(region: str) -> str:
    """
    Validate region parameter.
    
    Args:
        region: Region identifier
        
    Returns:
        Validated region string
        
    Raises:
        HTTPException: If region is invalid
    """
    if region not in VALID_REGIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region: {region}. Supported regions: {', '.join(VALID_REGIONS)}",
        )
    return region


def validate_temperature(temp: float) -> float:
    """Validate temperature is within reasonable range."""
    if not (TEMPERATURE_MIN <= temp <= TEMPERATURE_MAX):
        raise HTTPException(
            status_code=400,
            detail=f"Temperature must be between {TEMPERATURE_MIN}°C and {TEMPERATURE_MAX}°C. Got: {temp}°C",
        )
    return temp


def validate_wind_speed(speed: float) -> float:
    """Validate wind speed is within reasonable range."""
    if not (WIND_SPEED_MIN <= speed <= WIND_SPEED_MAX):
        raise HTTPException(
            status_code=400,
            detail=f"Wind speed must be between {WIND_SPEED_MIN} and {WIND_SPEED_MAX} m/s. Got: {speed} m/s",
        )
    return speed


def validate_solar_irradiance(irradiance: float) -> float:
    """Validate solar irradiance is within reasonable range."""
    if not (SOLAR_IRRADIANCE_MIN <= irradiance <= SOLAR_IRRADIANCE_MAX):
        raise HTTPException(
            status_code=400,
            detail=f"Solar irradiance must be between {SOLAR_IRRADIANCE_MIN} and {SOLAR_IRRADIANCE_MAX} W/m². Got: {irradiance} W/m²",
        )
    return irradiance
