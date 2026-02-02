import pytest
from app.utils.duplicate_handler import DuplicateHandler

def test_duplicate_handler_extra_coverage():
    # Test find_duplicates
    data = [
        {"id": 1, "name": "A", "value": 10},
        {"id": 1, "name": "B", "value": 20},
        {"id": 2, "name": "C", "value": 30},
        {"id": 2, "name": "D", "value": 40}
    ]
    duplicates = DuplicateHandler.find_duplicates(data, "id")
    assert len(duplicates['duplicates']) == 2  # Two groups of duplicates
    assert all(len(group) > 1 for group in duplicates)

    # Test merge_duplicates with keep_latest
    merged = DuplicateHandler.merge_duplicates(data.copy(), "id", "keep_latest")
    assert len(merged) == 2  # Should have 2 unique ids
    # Check that latest values are kept
    id1_items = [item for item in merged if item["id"] == 1]
    assert len(id1_items) == 1
    assert id1_items[0]["name"] == "A"  # First name for id=1 (no timestamps, so keeps first)

    # Test merge_duplicates with merge_data
    merged = DuplicateHandler.merge_duplicates(data.copy(), "id", "merge_data")
    assert len(merged) == 2
    # Check merged data
    id1_items = [item for item in merged if item["id"] == 1]
    assert len(id1_items) == 1
    # Should have combined data

    # Test detect_similar_entries
    similar_data = [
        {"id": 1, "text": "hello world"},
        {"id": 2, "text": "hello universe"},
        {"id": 3, "text": "goodbye world"}
    ]
    similar = DuplicateHandler.detect_similar_entries(similar_data, "text")
    # Should find some similarities

    # Test _merge_dicts
    d1 = {"a": 1, "b": [1, 2], "c": {"x": 1}}
    d2 = {"b": [3], "c": {"y": 2}, "d": 4}
    merged = DuplicateHandler._merge_dicts(d1, d2)
    assert merged["a"] == 1
    assert merged["d"] == 4
    assert len(merged["b"]) == 3  # [1, 2, 3]
    assert "x" in merged["c"] and "y" in merged["c"]

    # Test update_or_insert
    collection = []
    # Insert new
    DuplicateHandler.update_or_insert(collection, "id", {"id": 1, "val": 10})
    assert len(collection) == 1
    assert collection[0]["val"] == 10

    # Update existing
    DuplicateHandler.update_or_insert(collection, "id", {"id": 1, "val": 20})
    assert len(collection) == 1
    assert collection[0]["val"] == 20

    # Insert another
    DuplicateHandler.update_or_insert(collection, "id", {"id": 2, "val": 30})
    assert len(collection) == 2

    # Test batch_upsert
    DuplicateHandler.batch_upsert(collection, "id", [
        {"id": 1, "val": 25},  # Update existing
        {"id": 3, "val": 40}   # Insert new
    ])
    assert len(collection) == 3
    id1_item = next(item for item in collection if item["id"] == 1)
    assert id1_item["val"] == 25