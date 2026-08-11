"""Data contract for the offline ERCOT system-wide load training pipeline.

This module uses only the Python standard library so it can validate an input
extract before optional data-science dependencies are installed.  It is not a
runtime feature builder and is never imported by the production API.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
import math
from typing import Any
from zoneinfo import ZoneInfo


class TrainingContractError(ValueError):
    """Raised when an offline ERCOT training extract violates its contract."""


# The canonical input is already hourly and UTC-normalized.  ERCOT load
# observations are paired with weather values valid at the same timestamp.
ERCOT_RAW_COLUMNS = (
    "timestamp_utc",
    "actual_load_mw",
    "temperature_c",
    "wind_speed_ms",
    "solar_irradiance_wm2",
)

# These match the feature units exposed by the current GERT runtime.  Calendar
# and lagged-load features will be declared in the artifact manifest only when
# an operational feature store has been implemented.
SERVED_WEATHER_COLUMNS = (
    "temperature_c",
    "wind_speed_ms",
    "solar_irradiance_wm2",
)


def parse_utc_timestamp(value: Any) -> datetime:
    """Parse an ISO-8601 UTC timestamp and reject ambiguous local time."""
    if not isinstance(value, str) or not value.strip():
        raise TrainingContractError("timestamp_utc must be a non-empty ISO-8601 string")
    normalized = value.replace("Z", "+00:00")
    try:
        timestamp = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise TrainingContractError(f"Invalid timestamp_utc: {value!r}") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise TrainingContractError("timestamp_utc must be explicitly UTC")
    return timestamp.astimezone(timezone.utc)


def _positive_number(row: Mapping[str, Any], column: str) -> float:
    try:
        value = float(row[column])
    except (KeyError, TypeError, ValueError) as exc:
        raise TrainingContractError(f"{column} must be numeric") from exc
    if not math.isfinite(value):
        raise TrainingContractError(f"{column} must be finite")
    if column == "actual_load_mw" and value <= 0:
        raise TrainingContractError("actual_load_mw must be positive")
    return value


def validate_hourly_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Validate ordered, contiguous hourly ERCOT system-wide training rows.

    Missing intervals are rejected rather than silently filled: how to impute
    training data is a documented modelling decision, not an ingest default.
    """
    if not rows:
        raise TrainingContractError("Training extract contains no rows")

    previous: datetime | None = None
    for index, row in enumerate(rows):
        missing = [column for column in ERCOT_RAW_COLUMNS if column not in row]
        if missing:
            raise TrainingContractError(f"Row {index} missing required columns: {missing}")
        timestamp = parse_utc_timestamp(row["timestamp_utc"])
        for column in ERCOT_RAW_COLUMNS[1:]:
            _positive_number(row, column)
        if previous is not None:
            if timestamp <= previous:
                raise TrainingContractError("Rows must be strictly increasing by timestamp_utc")
            if timestamp - previous != timedelta(hours=1):
                raise TrainingContractError(
                    f"Rows must be contiguous hourly observations; gap after {previous.isoformat()}"
                )
        previous = timestamp


def calendar_features(timestamp_utc: datetime) -> dict[str, int]:
    """Return deterministic ERCOT market-local calendar features."""
    if timestamp_utc.tzinfo is None or timestamp_utc.utcoffset() != timedelta(0):
        raise TrainingContractError("calendar_features requires a UTC timestamp")
    local = timestamp_utc.astimezone(ZoneInfo("America/Chicago"))
    return {
        "hour": local.hour,
        "day_of_week": local.weekday(),
        "month": local.month,
        "is_weekend": int(local.weekday() >= 5),
    }
