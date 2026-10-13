from mlclient.xquery import cts, fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.distinctive_terms(fn.string("auxiliary"), options=node)
    return expression.compile()
