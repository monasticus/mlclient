"""Intersection serialization through the public CTS builder."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="are not and-query options") as error:
        cts.and_query([], options="bogus")
    assert str(error.value) == (
        "options ['bogus'] are not and-query options; use at mos"
        "t one of ordered, unordered"
    )
