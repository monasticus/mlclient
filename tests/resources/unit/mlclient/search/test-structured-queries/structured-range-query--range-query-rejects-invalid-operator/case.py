"""Test RangeQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import Element, RangeQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        RangeQuery(Element("price"), 1, operator=">")
    assert str(exc.value) == "Range operator must be LT, LE, GT, GE, EQ, or NE."
