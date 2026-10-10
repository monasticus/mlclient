"""Public compilation and native serialization of ReverseQuery."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    source = '<report xmlns:ns0="urn:reports" kind="ns0:blue" />'
    query = cts.reverse_query(FunctionCall("xdmp:unquote", (source,)))
    assert query.to_json() == {"reverseQuery": {"nodes": [source]}}
    with pytest.raises(TypeError) as error:
        query.to_xml()
    assert str(error.value) == (
        "cts:reverse-query: nodes: CTS XML namespace prefixes ns"
        "N conflict with ElementTree; use named prefixes or serv"
        "er evaluation."
    )
