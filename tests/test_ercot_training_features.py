from datetime import datetime, timedelta, timezone

import pytest

from training.ercot.contracts import TrainingContractError
from training.ercot.features import (
    OUTPUT_COLUMNS,
    build_serving_feature_rows,
    validate_serving_feature_rows,
)


def _raw_row(timestamp: datetime) -> dict:
    return {
        "timestamp_utc": timestamp.isoformat().replace("+00:00", "Z"),
        "actual_load_mw": 51000.0,
        "temperature_c": 35.0,
        "wind_speed_ms": 4.2,
        "solar_irradiance_wm2": 0.0,
    }


def test_build_serving_features_uses_runtime_contract_names():
    start = datetime(2025, 8, 1, tzinfo=timezone.utc)
    rows = [
        {**_raw_row(start + timedelta(hours=index)), "actual_load_mw": 50_000 + index}
        for index in range(169)
    ]
    result = build_serving_feature_rows(rows)
    assert tuple(result[0].keys()) == OUTPUT_COLUMNS
    assert result[0]["temperature"] == 35.0
    assert result[0]["solar_irradiance"] == 0.0
    assert result[0]["year"] == 2025.0
    assert result[0]["lag_load_1h"] == 50_167
    assert result[0]["lag_load_24h"] == 50_144
    assert result[0]["lag_load_168h"] == 50_000
    assert result[0]["rolling_load_mean_24h"] == pytest.approx(50_155.5)


def test_serving_feature_validation_rejects_missing_runtime_feature():
    with pytest.raises(TrainingContractError, match="missing columns"):
        validate_serving_feature_rows([
            {"timestamp_utc": "2025-08-01T00:00:00Z", "actual_load_mw": 50000, "temperature": 30}
        ])
