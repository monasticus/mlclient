from mlclient.xquery import cts, fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.similar_query(fn.string("auxiliary"), options=node)
    return expression.compile()
