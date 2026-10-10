"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts, fn


def run():
    with pytest.raises(TypeError) as error:
        cts.element_range_query("price", ">", fn.count(fn.doc())).serialize()
    assert str(error.value) == (
        "cts:element-range-query: value: CTS value argument requ"
        "ires server evaluation, got fn:count(fn:doc())."
    )
