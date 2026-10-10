import json
from mlclient.xquery import cts, fn, xdmp


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expected = xdmp.unquote(json.dumps(node)).xpath("node()")
    expression = cts.cluster(fn.string("auxiliary"), options=node)
    original = expression.compile()
    assert original == cts.cluster(fn.string("auxiliary"), options=expected).compile()
    assert "blue" not in original[0]
    assert any("blue" in str(value) for value in original[1].values())
    node["nested"][0]["count"] = 99
    assert expression.compile() == original
