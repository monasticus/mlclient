from mlclient.xquery import cts


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.contains(node, cts.true_query())
    return expression.compile()
