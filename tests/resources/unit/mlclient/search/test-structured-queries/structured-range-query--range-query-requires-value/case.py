"""Test RangeQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import Element, RangeQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        RangeQuery(Element("price"), [])
    assert str(exc.value) == "Range queries require at least one value."
