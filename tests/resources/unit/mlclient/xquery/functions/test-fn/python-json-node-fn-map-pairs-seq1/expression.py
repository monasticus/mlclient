from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.map_pairs(fn.string("auxiliary"), node, fn.string("auxiliary"))
    return expression.compile()
