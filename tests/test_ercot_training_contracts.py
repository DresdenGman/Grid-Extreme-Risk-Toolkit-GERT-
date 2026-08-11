from datetime import datetime, timedelta, timezone

import pytest

from training.ercot.contracts import (
    TrainingContractError,
    calendar_features,
    validate_hourly_rows,
)


def _row(timestamp: datetime, load: float = 50000.0) -> dict:
    return {
        "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "actual_load_mw": load,
        "temperature_c": 30.0,
        "wind_speed_ms": 5.0,
        "solar_irradiance_wm2": 700.0,
    }


def test_hourly_training_rows_are_validated_in_utc():
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    validate_hourly_rows([_row(start), _row(start + timedelta(hours=1))])


def test_hourly_training_rows_reject_gap():
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(TrainingContractError, match="contiguous"):
        validate_hourly_rows([_row(start), _row(start + timedelta(hours=2))])


def test_calendar_features_are_ercot_local_deterministic():
    timestamp = datetime(2025, 2, 2, 23, tzinfo=timezone.utc)
    assert calendar_features(timestamp) == {
        "hour": 17,
        "day_of_week": 6,
        "month": 2,
        "is_weekend": 1,
    }
