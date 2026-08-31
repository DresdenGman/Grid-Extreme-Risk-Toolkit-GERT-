import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

from training.ercot.build_feature_table import build_feature_table


def test_build_feature_table_writes_canonical_csv(tmp_path: Path):
    source = tmp_path / "joined.csv"
    output = tmp_path / "run" / "features.csv"
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    body = "".join(
        f"{(start + timedelta(hours=index)).isoformat().replace('+00:00', 'Z')},{50000 + index},20,4,0\n"
        for index in range(169)
    )
    source.write_text(
        "timestamp_utc,actual_load_mw,temperature_c,wind_speed_ms,solar_irradiance_wm2\n" + body,
        encoding="utf-8",
    )

    assert build_feature_table(source, output) == 1
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["temperature"] == "20.0"
    assert list(rows[0]) == [
        "timestamp_utc", "actual_load_mw", "temperature", "wind_speed", "solar_irradiance",
        "hour", "day_of_week", "month", "is_weekend", "year",
        "lag_load_1h", "lag_load_24h", "lag_load_168h",
        "rolling_load_mean_24h", "rolling_load_std_24h",
        "rolling_load_mean_168h", "rolling_load_std_168h",
    ]
