"""Build a serving-compatible ERCOT training feature table.

Schema 1.3 adds causal load lags and rolling statistics.  Every operational
feature is shifted by at least one hour, so the target observation can never
leak into its own feature row.  The production ERCOT adapter builds the same
feature names from official recent history.
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
    "lag_load_1h", "lag_load_24h", "lag_load_168h",
    "rolling_load_mean_24h", "rolling_load_std_24h",
    "rolling_load_mean_168h", "rolling_load_std_168h",
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
    base_rows: list[dict[str, float | str]] = []
    loads = [float(row["actual_load_mw"]) for row in rows]
    for index, row in enumerate(rows):
        if index < 168:
            continue
        calendar = calendar_features(parse_utc_timestamp(row["timestamp_utc"]))
        prior_24 = loads[index - 24:index]
        prior_168 = loads[index - 168:index]
        mean_24 = sum(prior_24) / len(prior_24)
        mean_168 = sum(prior_168) / len(prior_168)
        std_24 = (sum((value - mean_24) ** 2 for value in prior_24) / len(prior_24)) ** 0.5
        std_168 = (sum((value - mean_168) ** 2 for value in prior_168) / len(prior_168)) ** 0.5
        base_rows.append(
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
                "lag_load_1h": loads[index - 1],
                "lag_load_24h": loads[index - 24],
                "lag_load_168h": loads[index - 168],
                "rolling_load_mean_24h": mean_24,
                "rolling_load_std_24h": std_24,
                "rolling_load_mean_168h": mean_168,
                "rolling_load_std_168h": std_168,
            }
        )
    return base_rows


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
