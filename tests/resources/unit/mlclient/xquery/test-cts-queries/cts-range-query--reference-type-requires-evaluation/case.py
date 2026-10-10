"""Public compilation and native serialization of RangeQuery."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(TypeError) as error:
        cts.range_query(cts.element_reference("price"), "=", 2).serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference scalarType re"
        "quires an explicit option or server evaluation."
    )
