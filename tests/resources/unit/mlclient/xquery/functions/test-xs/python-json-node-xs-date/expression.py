from mlclient.xquery import xs


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = xs.date(node)
    return expression.compile()
