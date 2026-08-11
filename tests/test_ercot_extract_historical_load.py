from training.ercot.extract_historical_load import utc_rows


def _rows(day: str, count: int):
    return [
        {"OperDay": day, "HourEnding": str(i + 1), "TOTAL": "100", "NORTH": "40", "SOUTH": "20", "WEST": "10", "HOUSTON": "30", "DSTFlag": "N"}
        for i in range(count)
    ]


def test_utc_rows_handles_spring_forward_day() -> None:
    result = utc_rows(_rows("03/14/2021", 23))

    assert result[0]["timestamp_utc"] == "2021-03-14T06:00:00Z"
    assert result[-1]["timestamp_utc"] == "2021-03-15T04:00:00Z"


def test_utc_rows_handles_fall_back_day() -> None:
    result = utc_rows(_rows("11/07/2021", 25))

    assert result[0]["timestamp_utc"] == "2021-11-07T05:00:00Z"
    assert result[-1]["timestamp_utc"] == "2021-11-08T05:00:00Z"
