from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.insert_before(fn.string("auxiliary"), fn.string("auxiliary"), node)
    return expression.compile()
