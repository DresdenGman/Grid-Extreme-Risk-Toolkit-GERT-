"""Create a local, URL-free catalog of ERCOT NP6-346-CD historic files."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from data.ercot import ERCOTAdapter
from training.ercot.inspect_historical_archive import ARCHIVE_URL
from training.ercot.local_credentials import load_local_credentials


PAGE_SIZE = 1000
OUTPUT_PATH = Path("training_data/ercot_np6_346_archive_catalog.json")


def archive_record(item: dict[str, Any]) -> dict[str, str]:
    """Keep selectors only; a temporary signed download URL is never saved."""
    doc_id = item.get("docId")
    friendly_name = item.get("friendlyName")
    posted_at = item.get("postDatetime")
    if not isinstance(doc_id, (str, int)) or not str(doc_id):
        raise ValueError("ERCOT archive item is missing a document id")
    if not all(isinstance(value, str) and value for value in (friendly_name, posted_at)):
        raise ValueError("ERCOT archive item is missing a required selector")
    return {"doc_id": str(doc_id), "friendly_name": friendly_name, "post_datetime": posted_at}


async def fetch_catalog() -> list[dict[str, str]]:
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
        first = await client.get(ARCHIVE_URL, params={"page": 1, "size": PAGE_SIZE}, headers=headers)
        first.raise_for_status()
        first_payload = first.json()
        total_pages = first_payload.get("_meta", {}).get("totalPages")
        if not isinstance(total_pages, int) or total_pages < 1:
            raise ValueError("ERCOT archive response did not provide totalPages")

        payloads = [first_payload]
        for page in range(2, total_pages + 1):
            response = await client.get(
                ARCHIVE_URL, params={"page": page, "size": PAGE_SIZE}, headers=headers
            )
            response.raise_for_status()
            payloads.append(response.json())

    records: list[dict[str, str]] = []
    for payload in payloads:
        archives = payload.get("archives")
        if not isinstance(archives, list):
            raise ValueError("ERCOT archive response did not contain an archives list")
        records.extend(archive_record(item) for item in archives if isinstance(item, dict))
    return records


def main() -> None:
    records = asyncio.run(fetch_catalog())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} URL-free ERCOT archive records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
