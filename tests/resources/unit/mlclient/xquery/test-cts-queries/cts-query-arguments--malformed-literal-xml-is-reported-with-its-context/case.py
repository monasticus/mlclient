"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.reverse_query(FunctionCall("xdmp:unquote", ("<a><b></a>",)))
    with pytest.raises(ValueError, match="not well-formed") as error:
        query.to_xml()
    assert str(error.value) == (
        "cts:reverse-query: nodes: CTS literal XML is not well-f"
        "ormed: mismatched tag: line 1, column 8"
    )
