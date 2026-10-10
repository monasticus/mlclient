from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.local_name(node)
    return expression.compile()
