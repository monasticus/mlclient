"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import FunctionCall, cts


@pytest.mark.parametrize("method", ["to_json", "to_xml", "to_combined_query"])
@pytest.mark.parametrize("value", ["1", "0"])
def run(method, value):
    query = cts.json_property_value_query("v", FunctionCall("xs:boolean", (value,)))
    with pytest.raises(TypeError, match="value argument requires server evaluation"):
        getattr(query, method)()
