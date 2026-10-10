"""Public compilation and native serialization of RangeQuery."""

import pytest
from mlclient.xquery import cts


def run():
    query = cts.range_query(
        cts.element_attribute_reference("item", "amount", options="type=int"),
        "=",
        2,
    )
    with pytest.raises(TypeError) as error:
        query.to_json()
    assert str(error.value) == (
        "cts:range-query: reference: MarkLogic cannot read an el"
        "ement-attribute reference back from CTS JSON; serialize"
        " the query as XML or run it through eval"
    )
