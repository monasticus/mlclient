"""Public compilation and native serialization of RangeQuery."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(
        ValueError,
        match="Unsupported local CTS reference option",
    ) as error:
        cts.range_query(
            cts.element_reference("price", options="unknown"),
            "=",
            2,
        ).serialize()
    assert (
        str(error.value)
        == "cts:range-query: reference: Unsupported local CTS reference option: unknown"
    )
