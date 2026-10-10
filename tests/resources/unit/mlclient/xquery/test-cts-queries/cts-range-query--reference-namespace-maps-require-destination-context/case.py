"""Public compilation and native serialization of RangeQuery."""

import pytest
from mlclient.xquery import cts


def run():
    query = cts.range_query(
        cts.path_reference(
            "/r:report/r:price",
            options="type=int",
            namespaces={"r": "urn:reports"},
        ),
        "=",
        2,
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference namespace map"
        "s cannot be serialized natively; use EQNames in the pat"
        "h or destination database namespaces."
    )
