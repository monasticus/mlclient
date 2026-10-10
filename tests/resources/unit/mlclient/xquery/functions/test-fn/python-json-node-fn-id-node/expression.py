from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.id(fn.string("auxiliary"), node=node)
    return expression.compile()
