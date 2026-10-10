from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.key(fn.string("auxiliary"), fn.string("auxiliary"), top=node)
    return expression.compile()
