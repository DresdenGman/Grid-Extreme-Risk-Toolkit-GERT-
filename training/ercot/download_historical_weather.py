"""Download compact, reproducible ERA5 weather inputs for ERCOT training."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OUTPUT_DIR = Path("training_data/ercot_weather_era5")
VARIABLES = ("temperature_2m", "wind_speed_10m", "shortwave_radiation")
LOCATIONS = (
    ("NORTH", 32.7767, -96.7970),
    ("SOUTH", 29.4241, -98.4936),
    ("WEST", 31.9973, -102.0779),
    ("HOUSTON", 29.7604, -95.3698),
)


def normalize_payload(
    payload: Any, expected_hours: int, period_label: str
) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or len(payload) != len(LOCATIONS):
        raise ValueError("Open-Meteo must return one object per requested ERCOT location")
    normalized: list[dict[str, Any]] = []
    reference_times: list[str] | None = None
    for requested, item in zip(LOCATIONS, payload):
        if not isinstance(item, dict) or item.get("timezone") != "GMT":
            raise ValueError("Open-Meteo weather response must be UTC/GMT")
        hourly = item.get("hourly")
        units = item.get("hourly_units")
        if not isinstance(hourly, dict) or not isinstance(units, dict):
            raise ValueError("Open-Meteo response is missing hourly data or units")
        if units.get("temperature_2m") != "°C" or units.get("wind_speed_10m") != "m/s":
            raise ValueError("Open-Meteo temperature or wind unit mismatch")
        if units.get("shortwave_radiation") != "W/m²":
            raise ValueError("Open-Meteo radiation unit mismatch")
        times = hourly.get("time")
        if not isinstance(times, list) or len(times) != expected_hours:
            raise ValueError(f"Open-Meteo period {period_label} did not contain {expected_hours} hours")
        if reference_times is None:
            reference_times = times
        elif times != reference_times:
            raise ValueError("Open-Meteo locations returned different hourly timestamps")
        for variable in VARIABLES:
            values = hourly.get(variable)
            if not isinstance(values, list) or len(values) != expected_hours:
                raise ValueError(f"Open-Meteo variable {variable} is incomplete")
            if any(value is None for value in values):
                raise ValueError(f"Open-Meteo variable {variable} contains missing values")
        normalized.append(
            {
                "zone": requested[0],
                "requested_latitude": requested[1],
                "requested_longitude": requested[2],
                "source_latitude": item.get("latitude"),
                "source_longitude": item.get("longitude"),
                "hourly": {"time": times, **{name: hourly[name] for name in VARIABLES}},
            }
        )
    return normalized


def validate_payload(payload: Any, year: int) -> list[dict[str, Any]]:
    expected_hours = int(
        (
            datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            - datetime(year, 1, 1, tzinfo=timezone.utc)
        ).total_seconds()
        // 3600
    )
    return normalize_payload(payload, expected_hours, str(year))


def download_year(client: httpx.Client, year: int) -> list[dict[str, Any]]:
    response = client.get(
        ARCHIVE_URL,
        params={
            "latitude": ",".join(str(item[1]) for item in LOCATIONS),
            "longitude": ",".join(str(item[2]) for item in LOCATIONS),
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "hourly": ",".join(VARIABLES),
            "wind_speed_unit": "ms",
            "timezone": "UTC",
            "models": "era5",
        },
    )
    response.raise_for_status()
    return validate_payload(response.json(), year)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2019)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    if args.start_year > args.end_year:
        raise ValueError("start-year must not be after end-year")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120.0) as client:
        for year in range(args.start_year, args.end_year + 1):
            path = args.output_dir / f"{year}.json"
            if path.is_file():
                validate_payload(json.loads(path.read_text(encoding="utf-8"))["locations"], year)
                print(f"Reused validated ERA5 year {year}")
                continue
            locations = download_year(client, year)
            document = {
                "source": "Open-Meteo Historical Weather API",
                "model": "ERA5",
                "year": year,
                "locations": locations,
            }
            path.write_text(json.dumps(document, separators=(",", ":")) + "\n", encoding="utf-8")
            print(f"Downloaded and validated ERA5 year {year}")


if __name__ == "__main__":
    main()
