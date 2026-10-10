from mlclient.xquery import xs


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = xs.string(node)
    return expression.compile()
