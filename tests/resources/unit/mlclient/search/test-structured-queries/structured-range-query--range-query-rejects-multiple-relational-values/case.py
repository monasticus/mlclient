"""Test RangeQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import Element, RangeQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        RangeQuery(Element("price"), [1, 2], operator="GT")
    assert str(exc.value) == "Multiple range values require EQ or NE."
