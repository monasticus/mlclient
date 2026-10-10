from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.subsequence(node, fn.string("auxiliary"))
    return expression.compile()
