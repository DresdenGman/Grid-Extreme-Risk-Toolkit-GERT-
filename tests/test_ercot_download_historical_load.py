from datetime import date

from training.ercot.download_historical_load import output_path, selected_archives, valid_daily_zip


def test_selected_archives_filters_and_sorts_operating_days(tmp_path) -> None:
    payloads = [
        {"archives": [
            {"docId": 2, "postDatetime": "2020-01-02T05:50:00.000", "_links": {"endpoint": {"href": "b"}}},
            {"docId": 1, "postDatetime": "2020-01-01T05:50:00.000", "_links": {"endpoint": {"href": "a"}}},
            {"docId": 3, "postDatetime": "2021-01-01T05:50:00.000", "_links": {"endpoint": {"href": "c"}}},
        ]}
    ]

    selected = selected_archives(payloads, date(2020, 1, 1), date(2020, 1, 2))

    assert [item["docId"] for item in selected] == [1, 2]
    assert output_path(selected[0], tmp_path).name == "2020-01-01_1.zip"


def test_valid_daily_zip_rejects_non_zip_and_accepts_one_csv() -> None:
    assert not valid_daily_zip(b"not a zip")
