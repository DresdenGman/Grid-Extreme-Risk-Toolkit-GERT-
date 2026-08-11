import csv
from pathlib import Path

from training.ercot.build_feature_table import build_feature_table


def test_build_feature_table_writes_canonical_csv(tmp_path: Path):
    source = tmp_path / "joined.csv"
    output = tmp_path / "run" / "features.csv"
    source.write_text(
        "timestamp_utc,actual_load_mw,temperature_c,wind_speed_ms,solar_irradiance_wm2\n"
        "2025-01-01T00:00:00Z,50000,20,4,0\n"
        "2025-01-01T01:00:00Z,51000,19,5,0\n",
        encoding="utf-8",
    )

    assert build_feature_table(source, output) == 2
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["temperature"] == "20.0"
    assert list(rows[0]) == [
        "timestamp_utc", "actual_load_mw", "temperature", "wind_speed", "solar_irradiance",
        "hour", "day_of_week", "month", "is_weekend", "year"
    ]
