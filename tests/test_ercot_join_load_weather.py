import pandas as pd

from training.ercot.join_load_weather import aggregate_weather, training_zone_weights


def test_training_zone_weights_excludes_2025() -> None:
    load = pd.DataFrame(
        {
            "timestamp_utc": ["2024-01-01T06:00:00Z", "2025-01-01T06:00:00Z"],
            "north_mw": [40, 1000], "south_mw": [20, 0], "west_mw": [10, 0], "houston_mw": [30, 0],
        }
    )

    assert training_zone_weights(load) == {"NORTH": 0.4, "SOUTH": 0.2, "WEST": 0.1, "HOUSTON": 0.3}


def test_aggregate_weather_uses_fixed_zone_weights() -> None:
    weather = pd.DataFrame({"timestamp_utc": ["2024-01-01T00:00:00Z"]})
    for zone, value in {"NORTH": 10.0, "SOUTH": 20.0, "WEST": 30.0, "HOUSTON": 40.0}.items():
        for source in ("temperature_2m", "wind_speed_10m", "shortwave_radiation"):
            weather[f"{zone}_{source}"] = [value]

    result = aggregate_weather(weather, {"NORTH": 0.4, "SOUTH": 0.2, "WEST": 0.1, "HOUSTON": 0.3})

    assert result["temperature_c"].iloc[0] == 23.0
