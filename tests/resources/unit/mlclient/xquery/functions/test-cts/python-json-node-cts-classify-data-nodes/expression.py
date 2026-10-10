from mlclient.xquery import cts, fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.classify(node, fn.string("auxiliary"))
    return expression.compile()
