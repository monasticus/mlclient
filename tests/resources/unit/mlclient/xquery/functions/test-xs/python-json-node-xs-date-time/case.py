import json
from mlclient.xquery import xdmp, xs


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expected = xdmp.unquote(json.dumps(node)).xpath("node()")
    expression = xs.date_time(node)
    original = expression.compile()
    assert original == xs.date_time(expected).compile()
    assert "blue" not in original[0]
    assert any("blue" in str(value) for value in original[1].values())
    node["nested"][0]["count"] = 99
    assert expression.compile() == original
