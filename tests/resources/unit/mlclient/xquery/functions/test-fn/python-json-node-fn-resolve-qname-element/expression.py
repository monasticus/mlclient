from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.resolve_qname(fn.string("auxiliary"), node)
    return expression.compile()
