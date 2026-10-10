"""Public compilation and native serialization of ColumnRangeQuery."""

import pytest
from mlclient.xquery import cts


def run():
    query = cts.column_range_query("reports", "items", "price", 2)
    with pytest.raises(ValueError, match="CTS column ID must be") as error:
        query.with_column_id(-1)
    assert str(error.value) == "CTS column ID must be an unsigned 64-bit integer."
