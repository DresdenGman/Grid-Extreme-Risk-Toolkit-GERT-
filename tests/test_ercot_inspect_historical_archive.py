from training.ercot.inspect_historical_archive import response_shape


def test_response_shape_summarizes_list_without_values() -> None:
    assert response_shape([{"fileName": "secret.csv", "url": "https://signed.example"}]) == {
        "root_type": "list",
        "item_count": 1,
        "first_item_keys": ["fileName", "url"],
    }


def test_response_shape_summarizes_object_collection_without_values() -> None:
    assert response_shape({"data": [{"fileName": "secret.csv"}], "page": 1}) == {
        "root_type": "object",
        "top_level_keys": ["data", "page"],
        "collection_key": "data",
        "item_count": 1,
        "first_item_keys": ["fileName"],
    }


def test_response_shape_recognizes_archives_collection() -> None:
    assert response_shape({"archives": [{"fileName": "secret.csv"}]}) == {
        "root_type": "object",
        "top_level_keys": ["archives"],
        "collection_key": "archives",
        "item_count": 1,
        "first_item_keys": ["fileName"],
    }


def test_response_shape_keeps_link_relation_names_but_not_urls() -> None:
    assert response_shape({"archives": [{"_links": {"download": {"href": "https://signed.example"}}}]}) == {
        "root_type": "object",
        "top_level_keys": ["archives"],
        "collection_key": "archives",
        "item_count": 1,
        "first_item_keys": ["_links"],
        "first_item_link_relations": ["download"],
    }


def test_response_shape_includes_non_url_pagination_metadata() -> None:
    assert response_shape({"_meta": {"page": 1, "totalPages": 3, "url": "https://secret"}}) == {
        "root_type": "object",
        "top_level_keys": ["_meta"],
        "meta": {"page": 1, "totalPages": 3},
    }
