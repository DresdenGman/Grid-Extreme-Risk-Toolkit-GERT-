"""Audit the joined ERCOT/ERA5 training table before model fitting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


LOAD_PATH = Path("training_data/ercot_load_hourly_2019_2025.csv")
JOINED_PATH = Path("training_data/ercot_hourly_joined.csv")
OUTPUT_PATH = Path("training_runs/ercot_v1/data_quality.json")


def audit(load: pd.DataFrame, joined: pd.DataFrame) -> dict[str, object]:
    timestamps = pd.to_datetime(joined["timestamp_utc"], utc=True)
    gaps = timestamps.sort_values().diff().dropna()
    zone_sum = load[["north_mw", "south_mw", "west_mw", "houston_mw"]].sum(axis=1)
    total_difference = (load["actual_load_mw"] - zone_sum).abs()
    checks = {
        "no_duplicate_timestamps": not timestamps.duplicated().any(),
        "strictly_hourly": bool((gaps == pd.Timedelta(hours=1)).all()),
        "no_missing_values": not joined.isna().any().any(),
        "finite_numeric_values": bool(np.isfinite(joined.select_dtypes(include=["number"]).to_numpy()).all()),
        "positive_load": bool((joined["actual_load_mw"] > 0).all()),
        "temperature_physical_range": bool(joined["temperature_c"].between(-60, 60).all()),
        "nonnegative_wind": bool((joined["wind_speed_ms"] >= 0).all()),
        "nonnegative_solar": bool((joined["solar_irradiance_wm2"] >= 0).all()),
        "zonal_sum_matches_total_within_1_mw": bool((total_difference <= 1.0).all()),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "load_rows": int(len(load)),
        "joined_rows": int(len(joined)),
        "first_timestamp_utc": timestamps.min().isoformat(),
        "last_timestamp_utc": timestamps.max().isoformat(),
        "year_counts_ercot_local": {
            str(key): int(value)
            for key, value in timestamps.dt.tz_convert("America/Chicago").dt.year.value_counts().sort_index().items()
        },
        "ranges": {
            column: {"min": float(joined[column].min()), "max": float(joined[column].max())}
            for column in ("actual_load_mw", "temperature_c", "wind_speed_ms", "solar_irradiance_wm2")
        },
        "max_abs_total_minus_zone_sum_mw": float(total_difference.max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load", type=Path, default=LOAD_PATH)
    parser.add_argument("--joined", type=Path, default=JOINED_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    report = audit(pd.read_csv(args.load), pd.read_csv(args.joined))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit("ERCOT training data failed quality gates")


if __name__ == "__main__":
    main()
