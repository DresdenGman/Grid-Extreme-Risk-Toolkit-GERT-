"""Recover a missing NP6-346-CD archive day from ERCOT's tabular API."""

from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import date, timedelta
from pathlib import Path

import httpx

from data.ercot import ERCOTAdapter
from training.ercot.local_credentials import load_local_credentials


OUTPUT_DIR = Path("training_data/ercot_np6_346_supplemental")
OUTPUT_COLUMNS = ("OperDay", "HourEnding", "NORTH", "SOUTH", "WEST", "HOUSTON", "TOTAL", "DSTFlag")


async def fetch_day(day: date) -> list[dict[str, str]]:
    load_local_credentials()
    adapter = ERCOTAdapter()
    if not adapter.official_api_configured:
        raise RuntimeError("Local ERCOT credentials are required")
    async with httpx.AsyncClient(timeout=30.0) as client:
        token = await adapter._get_id_token(client)
        response = await client.get(
            adapter.LOAD_URL,
            params={
                "operatingDayFrom": day.isoformat(),
                "operatingDayTo": (day + timedelta(days=1)).isoformat(),
                "page": 1,
                "size": 100,
                "sort": "hourEnding",
                "dir": "ASC",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Ocp-Apim-Subscription-Key": adapter._subscription_key,
            },
        )
        response.raise_for_status()
    records = adapter._records(response.json())
    if len(records) not in (23, 24, 25):
        raise ValueError(f"Expected 23-25 ERCOT hourly rows for {day}, got {len(records)}")
    rows = []
    for record in records:
        rows.append(
            {
                "OperDay": day.strftime("%m/%d/%Y"),
                "HourEnding": str(record["hourEnding"]),
                "NORTH": str(record["north"]),
                "SOUTH": str(record["south"]),
                "WEST": str(record["west"]),
                "HOUSTON": str(record["houston"]),
                "TOTAL": str(record["total"]),
                "DSTFlag": str(record["DSTFlag"]),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", required=True, type=date.fromisoformat)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    rows = asyncio.run(fetch_day(args.day))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / f"{args.day.isoformat()}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Recovered {len(rows)} official ERCOT rows for {args.day} to {path}")


if __name__ == "__main__":
    main()
