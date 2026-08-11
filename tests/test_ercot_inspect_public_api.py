from training.ercot.inspect_public_api import sanitized_product_metadata


def test_sanitized_product_metadata_keeps_only_expected_fields() -> None:
    payload = {
        "emilId": "NP6-346-CD",
        "name": "Actual System Load by Forecast Zone",
        "status": "Active",
        "firstRun": "2010-01-01",
        "archiveDuration": 2555,
        "fileType": "csv",
        "downloadLimit": 1000,
        "secret": "must not persist",
        "_links": {
            "archive": {"href": "https://example.test/archive"},
            "self": {"href": "https://example.test/product"},
            "ignore": "not-a-link",
        },
    }

    assert sanitized_product_metadata(payload) == {
        "emilId": "NP6-346-CD",
        "name": "Actual System Load by Forecast Zone",
        "status": "Active",
        "firstRun": "2010-01-01",
        "archiveDuration": 2555,
        "fileType": "csv",
        "downloadLimit": 1000,
        "links": {
            "archive": "https://example.test/archive",
            "self": "https://example.test/product",
        },
    }
