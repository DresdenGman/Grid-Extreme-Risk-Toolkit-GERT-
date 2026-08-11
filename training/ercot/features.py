"""Build a serving-compatible ERCOT training feature table.

The first deployable ERCOT model deliberately uses only the three weather
inputs the production API can supply today.  Lagged load features are valuable
but require a separately operated feature store; training on them before that
store exists would create training-serving skew.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from zoneinfo import ZoneInfo

from training.ercot.contracts import (
    TrainingContractError,
    calendar_features,
    parse_utc_timestamp,
    validate_hourly_rows,
)


SERVED_FEATURE_COLUMNS = (
    "temperature", "wind_speed", "solar_irradiance",
    "hour", "day_of_week", "month", "is_weekend", "year",
)
OUTPUT_COLUMNS = ("timestamp_utc", "actual_load_mw", *SERVED_FEATURE_COLUMNS)


def build_serving_feature_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, float | str]]:
    """Create model-ready rows from validated hourly ERCOT observations.

    Input units are Celsius, m/s, and W/m².  Output names match GERT's
    ``WeatherFeatures`` / real-artifact contract exactly.
    """
    validate_hourly_rows(rows)
    features: list[dict[str, float | str]] = []
    for row in rows:
        calendar = calendar_features(parse_utc_timestamp(row["timestamp_utc"]))
        features.append(
            {
                "timestamp_utc": str(row["timestamp_utc"]),
                "actual_load_mw": float(row["actual_load_mw"]),
                "temperature": float(row["temperature_c"]),
                "wind_speed": float(row["wind_speed_ms"]),
                "solar_irradiance": float(row["solar_irradiance_wm2"]),
                **calendar,
                "year": float(
                    parse_utc_timestamp(row["timestamp_utc"])
                    .astimezone(ZoneInfo("America/Chicago"))
                    .year
                ),
            }
        )
    return features


def validate_serving_feature_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Validate the exact feature columns expected by the current real adapter."""
    if not rows:
        raise TrainingContractError("Serving feature table contains no rows")
    for index, row in enumerate(rows):
        missing = [column for column in OUTPUT_COLUMNS if column not in row]
        if missing:
            raise TrainingContractError(f"Feature row {index} missing columns: {missing}")
        try:
            load = float(row["actual_load_mw"])
            values = [float(row[column]) for column in SERVED_FEATURE_COLUMNS]
        except (TypeError, ValueError) as exc:
            raise TrainingContractError(f"Feature row {index} contains non-numeric values") from exc
        if load <= 0:
            raise TrainingContractError(f"Feature row {index} has non-positive load")
        if not all(value == value and abs(value) != float("inf") for value in values):
            raise TrainingContractError(f"Feature row {index} contains non-finite weather values")
