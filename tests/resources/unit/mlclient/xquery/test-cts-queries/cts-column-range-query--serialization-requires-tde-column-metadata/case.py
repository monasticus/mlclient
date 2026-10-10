"""Public compilation and native serialization of ColumnRangeQuery."""

import pytest
from mlclient.xquery import cts


def run():
    query = cts.column_range_query("reports", "items", "price", 2)
    message = (
        "cts:column-range-query: CTS column serialization requir"
        "es the destination database's TDE column ID; use with_c"
        "olumn_id()."
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == message
    with pytest.raises(TypeError) as error:
        query.to_xml()
    assert str(error.value) == message
