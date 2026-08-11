"""Resumably download official ERCOT NP6-346-CD daily archives for training.

The downloader is local-only. It observes ERCOT's 30 request/minute limit,
keeps raw ZIPs under Git-ignored ``training_data/``, and never persists a
token or a signed endpoint URL.
"""

from __future__ import annotations

import argparse
import asyncio
import zipfile
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx

from data.ercot import ERCOTAdapter
from training.ercot.inspect_historical_archive import ARCHIVE_URL
from training.ercot.local_credentials import load_local_credentials


# Archive post dates lag the embedded OperDay by one day.
DEFAULT_START = date(2019, 1, 2)
DEFAULT_END = date(2026, 1, 1)
PAGE_SIZE = 1000
REQUEST_INTERVAL_SECONDS = 2.1
OUTPUT_DIR = Path("training_data/ercot_np6_346_raw")


class RequestStartLimiter:
    """Maintain ERCOT's request-start interval without adding response latency."""

    def __init__(self, interval_seconds: float = REQUEST_INTERVAL_SECONDS) -> None:
        self.interval_seconds = interval_seconds
        self.last_started: float | None = None

    async def wait(self) -> None:
        loop = asyncio.get_running_loop()
        if self.last_started is not None:
            await asyncio.sleep(max(0.0, self.interval_seconds - (loop.time() - self.last_started)))
        self.last_started = loop.time()


def parse_day(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def selected_archives(payloads: list[dict[str, Any]], start: date, end: date) -> list[dict[str, Any]]:
    """Select daily archive records by their operating-day posting date."""
    selected: list[dict[str, Any]] = []
    for payload in payloads:
        archives = payload.get("archives")
        if not isinstance(archives, list):
            raise ValueError("ERCOT archive response did not contain an archives list")
        for item in archives:
            if not isinstance(item, dict):
                continue
            posted_at = item.get("postDatetime")
            endpoint = item.get("_links", {}).get("endpoint", {}).get("href")
            if not isinstance(posted_at, str) or not isinstance(endpoint, str):
                raise ValueError("ERCOT archive record is missing date or endpoint")
            if start <= parse_day(posted_at) <= end:
                selected.append(item)
    return sorted(selected, key=lambda item: str(item["postDatetime"]))


def output_path(item: dict[str, Any], output_dir: Path) -> Path:
    day = parse_day(str(item["postDatetime"])).isoformat()
    return output_dir / f"{day}_{item['docId']}.zip"


def valid_daily_zip(content: bytes) -> bool:
    """Require exactly one CSV member before considering a file complete."""
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            return len([name for name in archive.namelist() if name.lower().endswith(".csv")]) == 1
    except zipfile.BadZipFile:
        return False


async def fetch_payloads(
    client: httpx.AsyncClient, headers: dict[str, str], limiter: RequestStartLimiter
) -> list[dict[str, Any]]:
    await limiter.wait()
    first = await client.get(ARCHIVE_URL, params={"page": 1, "size": PAGE_SIZE}, headers=headers)
    first.raise_for_status()
    first_payload = first.json()
    total_pages = first_payload.get("_meta", {}).get("totalPages")
    if not isinstance(total_pages, int) or total_pages < 1:
        raise ValueError("ERCOT archive response did not provide totalPages")
    payloads = [first_payload]
    for page in range(2, total_pages + 1):
        await limiter.wait()
        response = await client.get(ARCHIVE_URL, params={"page": page, "size": PAGE_SIZE}, headers=headers)
        response.raise_for_status()
        payloads.append(response.json())
    return payloads


async def download(start: date, end: date, output_dir: Path) -> tuple[int, int]:
    load_local_credentials()
    adapter = ERCOTAdapter()
    if not adapter.official_api_configured:
        raise RuntimeError("Local ERCOT credentials are required")
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=60.0) as client:
        limiter = RequestStartLimiter()
        token = await adapter._get_id_token(client)
        headers = {
            "Authorization": f"Bearer {token}",
            "Ocp-Apim-Subscription-Key": adapter._subscription_key,
        }
        archives = selected_archives(await fetch_payloads(client, headers, limiter), start, end)
        if not archives:
            raise ValueError("No ERCOT archives matched the requested date range")

        downloaded = 0
        skipped = 0
        for index, item in enumerate(archives, start=1):
            path = output_path(item, output_dir)
            if path.is_file() and valid_daily_zip(path.read_bytes()):
                skipped += 1
                continue
            endpoint = item["_links"]["endpoint"]["href"]
            for attempt in range(1, 4):
                await limiter.wait()
                response = await client.get(endpoint, headers=headers)
                if response.status_code == 429 and attempt < 3:
                    await asyncio.sleep(30.0)
                    continue
                response.raise_for_status()
                if not valid_daily_zip(response.content):
                    raise ValueError(f"ERCOT archive {item['docId']} was not a valid one-CSV ZIP")
                path.write_bytes(response.content)
                downloaded += 1
                break
            if index % 25 == 0 or index == len(archives):
                print(f"Progress: {index}/{len(archives)} records; downloaded={downloaded}, reused={skipped}")
    return downloaded, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, default=DEFAULT_START)
    parser.add_argument("--end", type=date.fromisoformat, default=DEFAULT_END)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    downloaded, skipped = asyncio.run(download(args.start, args.end, args.output_dir))
    print(f"Complete: downloaded={downloaded}, reused={skipped}, output={args.output_dir}")


if __name__ == "__main__":
    main()
