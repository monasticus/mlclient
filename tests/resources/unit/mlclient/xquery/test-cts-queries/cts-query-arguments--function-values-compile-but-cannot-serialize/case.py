"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import FunctionCall, cts, xs


@pytest.mark.parametrize("method", ["to_json", "to_xml", "to_combined_query"])
@pytest.mark.parametrize(
    "value",
    [
        xs.integer(1.9),
        xs.date("2026-01-01"),
        FunctionCall("xs:double", (1.5,)),
        FunctionCall("xs:boolean", ("1",)),
        FunctionCall("xs:boolean", ("0",)),
        cts.uris(),
    ],
)
def run(method, value):
    query = cts.element_range_query("value", "=", value)
    (code, _) = query.compile()
    assert value.fn + "(" in code
    with pytest.raises(TypeError, match="value argument requires server evaluation"):
        getattr(query, method)()
