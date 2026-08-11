"""Save sanitized ERCOT Public API product metadata for offline training setup.

Run from the same shell session where the three ERCOT_API_* variables are set:

    python -m training.ercot.inspect_public_api

The command authenticates only to retrieve the public NP6-346-CD product
metadata.  It writes no credentials, tokens, or response headers to disk.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from data.ercot import ERCOTAdapter
from training.ercot.local_credentials import load_local_credentials


PRODUCT_URL = "https://api.ercot.com/api/public-reports/np6-346-cd"
OUTPUT_PATH = Path("training_data/ercot_np6_346_catalog.json")


def sanitized_product_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Retain only product/archive metadata useful for selecting downloads."""
    links = payload.get("_links", {})
    return {
        "emilId": payload.get("emilId"),
        "name": payload.get("name"),
        "status": payload.get("status"),
        "firstRun": payload.get("firstRun"),
        "archiveDuration": payload.get("archiveDuration"),
        "fileType": payload.get("fileType"),
        "downloadLimit": payload.get("downloadLimit"),
        "links": {
            name: value.get("href")
            for name, value in links.items()
            if isinstance(value, dict) and isinstance(value.get("href"), str)
        },
    }


async def inspect() -> dict[str, Any]:
    load_local_credentials()
    adapter = ERCOTAdapter()
    if not adapter.official_api_configured:
        raise RuntimeError("ERCOT_API_USERNAME, ERCOT_API_PASSWORD, and ERCOT_API_SUBSCRIPTION_KEY are required")

    async with httpx.AsyncClient(timeout=20.0) as client:
        token = await adapter._get_id_token(client)
        response = await client.get(
            PRODUCT_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Ocp-Apim-Subscription-Key": adapter._subscription_key,
            },
        )
        response.raise_for_status()
    return sanitized_product_metadata(response.json())


def main() -> None:
    metadata = asyncio.run(inspect())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote sanitized ERCOT product metadata to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
