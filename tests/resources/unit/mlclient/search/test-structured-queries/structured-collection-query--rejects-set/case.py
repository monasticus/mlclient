"""Structured components reject arguments they cannot serialize when built."""

import pytest
from mlclient.search.structured import CollectionQuery


def run():
    with pytest.raises(TypeError) as error:
        CollectionQuery({"a"})
    assert (
        str(error.value)
        == "CollectionQuery.uris must be a value or a sequence, got set"
    )
