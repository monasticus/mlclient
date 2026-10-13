"""Test structured-query target serialization."""

import pytest

from mlclient.search.structured import PathIndex


def test_path_index_is_hashable_and_keeps_a_copy_of_its_namespaces():
    namespaces = {"r": "https://example.com/example/reports"}
    index = PathIndex("/r:report", namespaces)
    namespaces["r"] = "https://example.com/changed"

    assert index.namespaces == {"r": "https://example.com/example/reports"}
    assert hash(index) == hash(
        PathIndex("/r:report", {"r": "https://example.com/example/reports"}),
    )
    with pytest.raises(TypeError):
        index.namespaces["r"] = "https://example.com/changed"
