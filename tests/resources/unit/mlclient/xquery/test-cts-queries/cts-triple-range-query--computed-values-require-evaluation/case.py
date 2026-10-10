"""Public compilation and native serialization of TripleRangeQuery."""

import pytest
from mlclient.xquery import cts, fn


def run():
    query = cts.triple_range_query(None, None, fn.doc("/value.xml"))
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:triple-range-query: object: CTS value argument requ"
        "ires server evaluation, got fn:doc('/value.xml')."
    )
