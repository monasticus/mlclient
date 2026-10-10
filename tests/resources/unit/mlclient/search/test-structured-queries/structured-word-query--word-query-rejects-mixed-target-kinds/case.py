"""Test WordQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import Element, JsonProperty, WordQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        WordQuery([Element("title"), JsonProperty("title")], "blue")
    assert str(exc.value) == "Use one non-empty target kind."
