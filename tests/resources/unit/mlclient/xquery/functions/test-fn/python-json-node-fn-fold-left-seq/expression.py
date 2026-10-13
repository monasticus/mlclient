from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.fold_left(fn.string("auxiliary"), fn.string("auxiliary"), node)
    return expression.compile()
