"""Join official ERCOT load with fixed-weight, four-zone ERA5 weather."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from training.ercot.download_historical_weather import LOCATIONS, VARIABLES


LOAD_PATH = Path("training_data/ercot_load_hourly_2019_2025.csv")
WEATHER_DIR = Path("training_data/ercot_weather_era5")
OUTPUT_PATH = Path("training_data/ercot_hourly_joined.csv")
MANIFEST_PATH = Path("training_runs/ercot_v1/data_manifest.json")
ZONE_LOAD_COLUMNS = {
    "NORTH": "north_mw",
    "SOUTH": "south_mw",
    "WEST": "west_mw",
    "HOUSTON": "houston_mw",
}


def training_zone_weights(load: pd.DataFrame, training_end_year: int = 2024) -> dict[str, float]:
    timestamps = pd.to_datetime(load["timestamp_utc"], utc=True)
    training = load.loc[
        timestamps.dt.tz_convert("America/Chicago").dt.year <= training_end_year
    ]
    totals = {zone: float(training[column].sum()) for zone, column in ZONE_LOAD_COLUMNS.items()}
    denominator = sum(totals.values())
    if denominator <= 0:
        raise ValueError("ERCOT training-period zonal load total must be positive")
    return {zone: value / denominator for zone, value in totals.items()}


def aggregate_weather(weather: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    result = pd.DataFrame({"timestamp_utc": weather["timestamp_utc"]})
    for source, target in (
        ("temperature_2m", "temperature_c"),
        ("wind_speed_10m", "wind_speed_ms"),
        ("shortwave_radiation", "solar_irradiance_wm2"),
    ):
        result[target] = sum(weather[f"{zone}_{source}"] * weight for zone, weight in weights.items())
    return result


def read_weather(weather_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in sorted(weather_dir.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        per_year: pd.DataFrame | None = None
        for location in document["locations"]:
            zone = location["zone"]
            hourly = location["hourly"]
            frame = pd.DataFrame(
                {
                    "timestamp_utc": pd.to_datetime(hourly["time"], utc=True),
                    **{f"{zone}_{name}": hourly[name] for name in VARIABLES},
                }
            )
            per_year = frame if per_year is None else per_year.merge(frame, on="timestamp_utc", validate="one_to_one")
        if per_year is None:
            raise ValueError(f"No weather locations found in {path}")
        frames.append(per_year)
    if not frames:
        raise FileNotFoundError(f"No ERA5 weather JSON files found in {weather_dir}")
    combined = pd.concat(frames, ignore_index=True).sort_values("timestamp_utc")
    duplicate_rows = combined.loc[combined["timestamp_utc"].duplicated(keep=False)]
    if not duplicate_rows.empty:
        value_columns = [column for column in combined.columns if column != "timestamp_utc"]
        conflicts = duplicate_rows.groupby("timestamp_utc")[value_columns].nunique(dropna=False)
        if (conflicts > 1).any().any():
            raise ValueError("Overlapping ERA5 files contain conflicting hourly values")
        combined = combined.drop_duplicates("timestamp_utc", keep="first")
    return combined.sort_values("timestamp_utc")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load", type=Path, default=LOAD_PATH)
    parser.add_argument("--weather-dir", type=Path, default=WEATHER_DIR)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--training-end-year", type=int, default=2024)
    args = parser.parse_args()
    load = pd.read_csv(args.load)
    load["timestamp_utc"] = pd.to_datetime(load["timestamp_utc"], utc=True)
    weights = training_zone_weights(load, args.training_end_year)
    weather = aggregate_weather(read_weather(args.weather_dir), weights)
    joined = load.merge(weather, on="timestamp_utc", how="inner", validate="one_to_one")
    joined = joined[["timestamp_utc", "actual_load_mw", "temperature_c", "wind_speed_ms", "solar_irradiance_wm2"]]
    joined["timestamp_utc"] = joined["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joined.to_csv(args.output, index=False)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "load_source": "ERCOT NP6-346-CD official archives and tabular recovery",
        "weather_source": "Open-Meteo Historical Weather API, ERA5",
        "weather_locations": [
            {"zone": zone, "latitude": latitude, "longitude": longitude}
            for zone, latitude, longitude in LOCATIONS
        ],
        "weather_weights_training_period": f"2019-01-01/{args.training_end_year}-12-31",
        "weather_weights": weights,
        "load_rows": int(len(load)),
        "joined_rows": int(len(joined)),
        "unmatched_boundary_rows": int(len(load) - len(joined)),
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(joined)} joined ERCOT/ERA5 hourly rows to {args.output}")
    print(f"Fixed weather weights: {weights}")


if __name__ == "__main__":
    main()
