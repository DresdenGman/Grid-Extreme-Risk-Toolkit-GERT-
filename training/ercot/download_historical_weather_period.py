"""Download a non-overlapping partial-year ERA5 period for fresh evaluation."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import httpx

from training.ercot.download_historical_weather import (
    ARCHIVE_URL,
    LOCATIONS,
    OUTPUT_DIR,
    VARIABLES,
    normalize_payload,
)


def download_period(client: httpx.Client, start: date, end: date) -> list[dict]:
    if start > end:
        raise ValueError("start must not be after end")
    response = client.get(
        ARCHIVE_URL,
        params={
            "latitude": ",".join(str(item[1]) for item in LOCATIONS),
            "longitude": ",".join(str(item[2]) for item in LOCATIONS),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": ",".join(VARIABLES),
            "wind_speed_unit": "ms",
            "timezone": "UTC",
            "models": "era5",
        },
    )
    response.raise_for_status()
    expected_hours = ((end - start).days + 1) * 24
    return normalize_payload(response.json(), expected_hours, f"{start}/{end}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / f"{args.start.isoformat()}_{args.end.isoformat()}.json"
    expected_hours = ((args.end - args.start).days + 1) * 24
    if path.is_file():
        document = json.loads(path.read_text(encoding="utf-8"))
        normalize_payload(document["locations"], expected_hours, f"{args.start}/{args.end}")
        print(f"Reused validated ERA5 period {args.start}/{args.end}")
        return
    with httpx.Client(timeout=120.0) as client:
        locations = download_period(client, args.start, args.end)
    document = {
        "source": "Open-Meteo Historical Weather API",
        "model": "ERA5",
        "period": {"start": args.start.isoformat(), "end": args.end.isoformat()},
        "locations": locations,
    }
    path.write_text(json.dumps(document, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Downloaded and validated ERA5 period {args.start}/{args.end} to {path}")


if __name__ == "__main__":
    main()
