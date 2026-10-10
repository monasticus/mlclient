"""Public compilation and native serialization of ReverseQuery."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ('{"label":"blue"}',)).xpath("*"),
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:reverse-query: nodes: CTS JSON model-node projectio"
        "ns require server evaluation."
    )
