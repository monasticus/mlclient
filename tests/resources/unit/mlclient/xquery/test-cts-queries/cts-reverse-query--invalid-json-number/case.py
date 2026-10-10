"""Public compilation and native serialization of ReverseQuery."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.reverse_query(FunctionCall("xdmp:unquote", ('{"count":NaN}',)))
    with pytest.raises(
        ValueError,
        match="Invalid CTS model-node JSON constant",
    ) as error:
        query.serialize()
    assert (
        str(error.value)
        == "cts:reverse-query: nodes: Invalid CTS model-node JSON constant: NaN"
    )
