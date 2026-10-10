import json
from mlclient.xquery import fn, xdmp


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expected = xdmp.unquote(json.dumps(node)).xpath("node()")
    expression = fn.nilled(node)
    original = expression.compile()
    assert original == fn.nilled(expected).compile()
    assert "blue" not in original[0]
    assert any("blue" in str(value) for value in original[1].values())
    node["nested"][0]["count"] = 99
    assert expression.compile() == original
