from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.insert_before(node, fn.string("auxiliary"), fn.string("auxiliary"))
    return expression.compile()
