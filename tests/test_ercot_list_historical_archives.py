import pytest

from training.ercot.list_historical_archives import archive_record


def test_archive_record_drops_links_and_keeps_selectors() -> None:
    assert archive_record(
        {
            "docId": "123",
            "friendlyName": "load.csv",
            "postDatetime": "2025-01-01T00:00:00Z",
            "_links": {"download": {"href": "https://signed.example"}},
        }
    ) == {
        "doc_id": "123",
        "friendly_name": "load.csv",
        "post_datetime": "2025-01-01T00:00:00Z",
    }


def test_archive_record_normalizes_numeric_document_id() -> None:
    assert archive_record(
        {"docId": 123, "friendlyName": "load.csv", "postDatetime": "2025-01-01T00:00:00Z"}
    )["doc_id"] == "123"


def test_archive_record_rejects_missing_selector() -> None:
    with pytest.raises(ValueError):
        archive_record({"docId": "123", "friendlyName": "load.csv"})
