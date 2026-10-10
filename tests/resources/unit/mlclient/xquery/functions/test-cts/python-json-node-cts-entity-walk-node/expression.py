from mlclient.xquery import cts, fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.entity_walk(node, fn.string("auxiliary"))
    return expression.compile()
