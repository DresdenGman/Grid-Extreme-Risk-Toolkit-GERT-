"""Extract official ERCOT daily archives into one DST-correct UTC load table."""

from __future__ import annotations

import argparse
import csv
import io
import zipfile
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


MARKET_TIMEZONE = ZoneInfo("America/Chicago")
RAW_DIR = Path("training_data/ercot_np6_346_raw")
SUPPLEMENTAL_DIR = Path("training_data/ercot_np6_346_supplemental")
OUTPUT_PATH = Path("training_data/ercot_load_hourly_2019_2025.csv")
OUTPUT_COLUMNS = ("timestamp_utc", "actual_load_mw", "north_mw", "south_mw", "west_mw", "houston_mw")


def operating_day(rows: list[dict[str, str]]) -> date:
    days = {datetime.strptime(row["OperDay"], "%m/%d/%Y").date() for row in rows}
    if len(days) != 1:
        raise ValueError("ERCOT daily file must contain exactly one OperDay")
    return days.pop()


def utc_rows(rows: list[dict[str, str]]) -> list[dict[str, float | str]]:
    day = operating_day(rows)
    start_local = datetime.combine(day, time.min, tzinfo=MARKET_TIMEZONE)
    end_local = datetime.combine(day + timedelta(days=1), time.min, tzinfo=MARKET_TIMEZONE)
    start_utc = start_local.astimezone(timezone.utc)
    expected = int((end_local.astimezone(timezone.utc) - start_utc).total_seconds() // 3600)
    if len(rows) != expected:
        raise ValueError(f"ERCOT {day} has {len(rows)} rows; DST calendar requires {expected}")
    result = []
    for index, row in enumerate(rows):
        result.append(
            {
                "timestamp_utc": (start_utc + timedelta(hours=index)).isoformat().replace("+00:00", "Z"),
                "actual_load_mw": float(row["TOTAL"]),
                "north_mw": float(row["NORTH"]),
                "south_mw": float(row["SOUTH"]),
                "west_mw": float(row["WEST"]),
                "houston_mw": float(row["HOUSTON"]),
            }
        )
    return result


def read_zip(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"Expected one CSV in {path}")
        return list(csv.DictReader(io.TextIOWrapper(archive.open(names[0]), encoding="utf-8-sig")))


def build_rows(raw_dir: Path, supplemental_dir: Path, start: date, end: date) -> list[dict[str, float | str]]:
    by_day: dict[date, list[dict[str, str]]] = {}
    for path in sorted(raw_dir.glob("*.zip")):
        rows = read_zip(path)
        day = operating_day(rows)
        if start <= day <= end:
            if day in by_day:
                raise ValueError(f"Duplicate ERCOT operating day: {day}")
            by_day[day] = rows
    if supplemental_dir.is_dir():
        for path in sorted(supplemental_dir.glob("*.csv")):
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            day = operating_day(rows)
            if start <= day <= end:
                by_day[day] = rows
    result = [row for day in sorted(by_day) for row in utc_rows(by_day[day])]
    expected_start = datetime.combine(start, time.min, tzinfo=MARKET_TIMEZONE).astimezone(timezone.utc)
    expected_end = datetime.combine(end + timedelta(days=1), time.min, tzinfo=MARKET_TIMEZONE).astimezone(timezone.utc)
    if not result or result[0]["timestamp_utc"] != expected_start.isoformat().replace("+00:00", "Z"):
        raise ValueError("ERCOT load extract does not start at the requested operating day")
    timestamps = [datetime.fromisoformat(str(row["timestamp_utc"]).replace("Z", "+00:00")) for row in result]
    if any(b - a != timedelta(hours=1) for a, b in zip(timestamps, timestamps[1:])):
        raise ValueError("ERCOT load extract contains an hourly gap")
    if timestamps[-1] + timedelta(hours=1) != expected_end:
        raise ValueError("ERCOT load extract does not end at the requested operating day")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--supplemental-dir", type=Path, default=SUPPLEMENTAL_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2019, 1, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2025, 12, 31))
    args = parser.parse_args()
    rows = build_rows(args.raw_dir, args.supplemental_dir, args.start, args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} contiguous official ERCOT hourly load rows to {args.output}")


if __name__ == "__main__":
    main()
