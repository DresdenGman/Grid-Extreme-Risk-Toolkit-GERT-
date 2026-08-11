from training.ercot.download_historical_weather import LOCATIONS, VARIABLES, validate_payload


def _payload(hours: int):
    times = [f"2019-01-01T{hour:02d}:00" for hour in range(hours)]
    return [
        {
            "timezone": "GMT",
            "latitude": latitude,
            "longitude": longitude,
            "hourly_units": {
                "temperature_2m": "°C",
                "wind_speed_10m": "m/s",
                "shortwave_radiation": "W/m²",
            },
            "hourly": {
                "time": times,
                **{variable: [1.0] * hours for variable in VARIABLES},
            },
        }
        for _, latitude, longitude in LOCATIONS
    ]


def test_validate_payload_accepts_complete_non_leap_year() -> None:
    result = validate_payload(_payload(8760), 2019)

    assert [item["zone"] for item in result] == [item[0] for item in LOCATIONS]
