"""CLI for producing a serving-compatible ERCOT training feature CSV.

Usage:
    python -m training.ercot.build_feature_table \
      --input training_data/ercot_hourly_joined.csv \
      --output training_runs/ercot_v1/features.csv

The input is a locally assembled hourly load/weather extract. This command does
not fetch data, invoke Railway, or access any research-project path.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from training.ercot.features import OUTPUT_COLUMNS, build_serving_feature_rows


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Training input file not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_feature_table(rows: list[dict[str, float | str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_feature_table(input_path: Path, output_path: Path) -> int:
    """Read, validate, transform, and write a canonical feature table."""
    rows = build_serving_feature_rows(read_csv_rows(input_path))
    write_feature_table(rows, output_path)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    count = build_feature_table(args.input, args.output)
    print(f"Wrote {count} ERCOT serving-compatible feature rows to {args.output}")


if __name__ == "__main__":
    main()
