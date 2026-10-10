from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.deep_equal(node, fn.string("auxiliary"))
    return expression.compile()
