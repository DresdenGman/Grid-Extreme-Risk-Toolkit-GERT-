from datetime import datetime, timedelta, timezone

import pytest

from data.ercot import ERCOTAdapter


def test_historical_totals_normalizes_market_rows() -> None:
    payload = {
        "data": [
            {"OperDay": "08/01/2026", "HourEnding": f"{hour:02d}:00", "TOTAL": 40_000 + hour}
            for hour in range(1, 25)
        ]
    }

    rows = ERCOTAdapter._historical_totals(payload)

    assert len(rows) == 24
    assert rows[0][0].tzinfo == timezone.utc
    assert rows[0][1] == 40_001
    assert rows[-1][1] == 40_024


def test_operational_features_are_causal_and_complete() -> None:
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    series = [(start + timedelta(hours=index), 50_000.0 + index) for index in range(168)]
    target = start + timedelta(hours=168)

    features, as_of = ERCOTAdapter.operational_features_from_series(series, target)

    assert as_of == target - timedelta(hours=1)
    assert features["lag_load_1h"] == 50_167
    assert features["lag_load_24h"] == 50_144
    assert features["lag_load_168h"] == 50_000
    assert features["rolling_load_mean_24h"] == pytest.approx(50_155.5)
    assert features["rolling_load_mean_168h"] == pytest.approx(50_083.5)


def test_operational_features_reject_gaps() -> None:
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    series = [(start + timedelta(hours=index), 50_000.0) for index in range(168)]
    series[-20] = (series[-20][0] + timedelta(hours=1), series[-20][1])

    with pytest.raises(ValueError, match="not contiguous"):
        ERCOTAdapter.operational_features_from_series(
            series, start + timedelta(hours=168)
        )


def test_operational_features_reject_stale_history() -> None:
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    series = [(start + timedelta(hours=index), 50_000.0) for index in range(168)]

    with pytest.raises(ValueError, match="too stale"):
        ERCOTAdapter.operational_features_from_series(
            series, start + timedelta(hours=180)
        )
