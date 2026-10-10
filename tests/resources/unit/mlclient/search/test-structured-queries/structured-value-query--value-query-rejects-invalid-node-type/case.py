"""Test ValueQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import JsonProperty, ValueQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        ValueQuery(JsonProperty("active"), True, node_type="date")
    assert str(exc.value) == "JSON node type must be string, boolean, null, or number."
