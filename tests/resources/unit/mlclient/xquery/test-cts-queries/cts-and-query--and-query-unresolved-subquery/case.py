"""Intersection serialization through the public CTS builder."""

import pytest
from mlclient.xquery import cts, fn


def run():
    with pytest.raises(TypeError) as error:
        cts.and_query(fn.string("blue")).serialize()
    assert str(error.value) == (
        "cts:and-query: queries: CTS subquery requires server ev"
        "aluation, got fn:string('blue')."
    )
