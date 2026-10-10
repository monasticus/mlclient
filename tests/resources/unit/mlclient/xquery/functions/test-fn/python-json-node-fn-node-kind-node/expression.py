from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.node_kind(node)
    return expression.compile()
