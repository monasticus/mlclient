"""Test WordQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import Attribute, JsonProperty, WordQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        WordQuery(JsonProperty("title"), "blue", attribute=Attribute("name"))
    assert str(exc.value) == "Attribute selectors require Element targets."
