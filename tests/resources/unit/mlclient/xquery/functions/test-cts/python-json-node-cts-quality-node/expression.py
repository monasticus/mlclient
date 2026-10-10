from mlclient.xquery import cts


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.quality(node=node)
    return expression.compile()
