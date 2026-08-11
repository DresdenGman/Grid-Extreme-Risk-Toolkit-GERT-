"""Download one current ERCOT archive file and keep only its CSV header."""

from __future__ import annotations

import asyncio
import csv
import io
import json
from pathlib import Path
from typing import Any
import zipfile

import httpx

from data.ercot import ERCOTAdapter
from training.ercot.inspect_historical_archive import ARCHIVE_URL
from training.ercot.local_credentials import load_local_credentials


OUTPUT_PATH = Path("training_data/ercot_np6_346_sample_schema.json")


def csv_header(content: bytes) -> list[str]:
    """Extract CSV column names only; reject non-CSV or empty content."""
    rows = csv.reader(io.StringIO(content.decode("utf-8-sig")))
    header = next(rows, None)
    if not header:
        raise ValueError("ERCOT sample file did not contain a CSV header")
    return header


def sample_csv_content(content: bytes) -> tuple[str, bytes]:
    """Return CSV bytes from a direct CSV or one CSV inside an archive."""
    buffer = io.BytesIO(content)
    if not zipfile.is_zipfile(buffer):
        return "csv", content
    with zipfile.ZipFile(buffer) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError("Expected exactly one CSV inside the ERCOT archive sample")
        return "zip", archive.read(names[0])


def operational_time_summary(content: bytes) -> dict[str, Any]:
    """Summarize timestamp fields only; never retain load values."""
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
    if not rows:
        raise ValueError("ERCOT sample CSV did not contain data rows")
    operating_days = [row.get("OperDay", "") for row in rows]
    hour_endings = sorted({row.get("HourEnding", "") for row in rows})
    return {
        "row_count": len(rows),
        "operating_day_min": min(operating_days),
        "operating_day_max": max(operating_days),
        "hour_endings": hour_endings,
    }


async def inspect() -> dict[str, Any]:
    load_local_credentials()
    adapter = ERCOTAdapter()
    if not adapter.official_api_configured:
        raise RuntimeError("Local ERCOT credentials are required")

    async with httpx.AsyncClient(timeout=30.0) as client:
        token = await adapter._get_id_token(client)
        headers = {
            "Authorization": f"Bearer {token}",
            "Ocp-Apim-Subscription-Key": adapter._subscription_key,
        }
        archive_response = await client.get(
            ARCHIVE_URL, params={"page": 1, "size": 1}, headers=headers
        )
        archive_response.raise_for_status()
        item = archive_response.json()["archives"][0]
        endpoint = item.get("_links", {}).get("endpoint", {}).get("href")
        if not isinstance(endpoint, str) or not endpoint:
            raise ValueError("ERCOT archive item did not provide a file endpoint")
        sample_response = await client.get(endpoint, headers=headers)
        sample_response.raise_for_status()

    source_format, csv_content = sample_csv_content(sample_response.content)
    return {
        "content_type": sample_response.headers.get("content-type", ""),
        "content_disposition_present": bool(sample_response.headers.get("content-disposition")),
        "source_format": source_format,
        "csv_header": csv_header(csv_content),
        "operational_time_summary": operational_time_summary(csv_content),
    }


def main() -> None:
    schema = asyncio.run(inspect())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote ERCOT sample CSV schema to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
