from mlclient.xquery import cts


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.parse(cts.true_query(), bindings=node)
    return expression.compile()
