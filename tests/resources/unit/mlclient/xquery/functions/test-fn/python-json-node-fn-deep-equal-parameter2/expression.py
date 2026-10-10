from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.deep_equal(fn.string("auxiliary"), node)
    return expression.compile()
