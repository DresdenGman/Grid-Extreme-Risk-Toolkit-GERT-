from data.ercot import ERCOTAdapter
from services.region import ERCOT_SYSTEM_WEATHER_POINTS, ERCOT_SYSTEM_WEATHER_WEIGHTS


def test_aggregate_system_weather_uses_fixed_weights() -> None:
    payload = []
    expected = 0.0
    for index, (zone, _, _) in enumerate(ERCOT_SYSTEM_WEATHER_POINTS, start=1):
        value = float(index * 10)
        expected += value * ERCOT_SYSTEM_WEATHER_WEIGHTS[zone]
        payload.append(
            {"hourly": {"time": ["2026-01-01T01:00"], "temperature_2m": [value], "wind_speed_10m": [value], "shortwave_radiation": [value]}}
        )

    result = ERCOTAdapter._aggregate_system_weather(payload, "2026-01-01T01:00")

    assert abs(result["temperature_2m"] - expected) < 1e-9
