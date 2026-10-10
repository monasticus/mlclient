"""Test WordQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import PathIndex, WordQuery


def run():
    with pytest.raises(TypeError, match=r""".+""") as exc:
        WordQuery(PathIndex("/title"), "blue")
    assert str(exc.value) == "Targets must be Element, JsonProperty or Field instances."
