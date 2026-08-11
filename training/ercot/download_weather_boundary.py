"""Download one UTC boundary day needed by the ERCOT operating-day extract."""

from __future__ import annotations

import json
from datetime import date, timedelta

import httpx

from training.ercot.download_historical_weather import (
    ARCHIVE_URL,
    LOCATIONS,
    OUTPUT_DIR,
    VARIABLES,
    normalize_payload,
)


BOUNDARY_DAY = date(2026, 1, 1)


def main() -> None:
    response = httpx.get(
        ARCHIVE_URL,
        params={
            "latitude": ",".join(str(item[1]) for item in LOCATIONS),
            "longitude": ",".join(str(item[2]) for item in LOCATIONS),
            "start_date": BOUNDARY_DAY.isoformat(),
            "end_date": BOUNDARY_DAY.isoformat(),
            "hourly": ",".join(VARIABLES),
            "wind_speed_unit": "ms",
            "timezone": "UTC",
            "models": "era5",
        },
        timeout=60.0,
    )
    response.raise_for_status()
    locations = normalize_payload(response.json(), 24, BOUNDARY_DAY.isoformat())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{BOUNDARY_DAY.isoformat()}.json"
    path.write_text(
        json.dumps(
            {
                "source": "Open-Meteo Historical Weather API",
                "model": "ERA5",
                "period": BOUNDARY_DAY.isoformat(),
                "locations": locations,
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Downloaded and validated ERA5 boundary day {BOUNDARY_DAY} to {path}")


if __name__ == "__main__":
    main()
