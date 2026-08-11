"""Inspect the schema of one ERCOT historical-archive response safely.

This command requests a single archive page and stores only response shape and
field names.  It deliberately excludes any download URL, token, or file data.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from data.ercot import ERCOTAdapter
from training.ercot.local_credentials import load_local_credentials


ARCHIVE_URL = "https://api.ercot.com/api/public-reports/archive/np6-346-cd"
OUTPUT_PATH = Path("training_data/ercot_np6_346_archive_schema.json")


def response_shape(payload: Any) -> dict[str, Any]:
    """Return a value-free schema summary of a JSON archive response."""
    if isinstance(payload, list):
        first = payload[0] if payload else None
        return {
            "root_type": "list",
            "item_count": len(payload),
            "first_item_keys": sorted(first) if isinstance(first, dict) else [],
        }
    if isinstance(payload, dict):
        summary: dict[str, Any] = {
            "root_type": "object",
            "top_level_keys": sorted(payload),
        }
        meta = payload.get("_meta")
        if isinstance(meta, dict):
            summary["meta"] = {
                str(key): value
                for key, value in meta.items()
                if isinstance(value, (bool, int, float))
                or (isinstance(value, str) and "url" not in str(key).lower())
            }
        for collection_key in ("data", "items", "content", "archives", "_embedded"):
            collection = payload.get(collection_key)
            if isinstance(collection, list):
                first = collection[0] if collection else None
                summary["collection_key"] = collection_key
                summary["item_count"] = len(collection)
                summary["first_item_keys"] = sorted(first) if isinstance(first, dict) else []
                if isinstance(first, dict) and isinstance(first.get("_links"), dict):
                    summary["first_item_link_relations"] = sorted(first["_links"])
                break
        return summary
    return {"root_type": type(payload).__name__}


async def inspect() -> dict[str, Any]:
    load_local_credentials()
    adapter = ERCOTAdapter()
    if not adapter.official_api_configured:
        raise RuntimeError("Local ERCOT credentials are required")

    async with httpx.AsyncClient(timeout=20.0) as client:
        token = await adapter._get_id_token(client)
        response = await client.get(
            ARCHIVE_URL,
            params={"page": 1, "size": 1},
            headers={
                "Authorization": f"Bearer {token}",
                "Ocp-Apim-Subscription-Key": adapter._subscription_key,
            },
        )
        response.raise_for_status()
    return response_shape(response.json())


def main() -> None:
    schema = asyncio.run(inspect())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote sanitized ERCOT archive schema to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
