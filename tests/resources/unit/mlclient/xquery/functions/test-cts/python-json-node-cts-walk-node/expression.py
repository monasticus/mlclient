from mlclient.xquery import cts, fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.walk(node, cts.true_query(), fn.string("auxiliary"))
    return expression.compile()
