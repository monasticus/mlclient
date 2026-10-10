"""Public compilation and native serialization of RangeQuery."""

import pytest
from mlclient.xquery import cts, fn


def run():
    with pytest.raises(TypeError) as error:
        cts.range_query(fn.doc("/reference.xml"), "=", 2).serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference argument requ"
        "ires server evaluation, got fn:doc('/reference.xml')."
    )
