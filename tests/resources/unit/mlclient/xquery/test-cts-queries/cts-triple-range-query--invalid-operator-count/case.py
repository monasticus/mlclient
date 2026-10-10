"""Public compilation and native serialization of TripleRangeQuery."""

import pytest
from mlclient.xquery import cts


def run():
    query = cts.triple_range_query(None, None, 2, operator=["=", "="])
    with pytest.raises(
        ValueError,
        match="CTS triple operator requires one or three values",
    ) as error:
        query.serialize()
    assert (
        str(error.value)
        == "cts:triple-range-query: CTS triple operator requires one or three values."
    )
