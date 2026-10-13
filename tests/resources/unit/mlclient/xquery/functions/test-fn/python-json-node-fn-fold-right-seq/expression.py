from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.fold_right(fn.string("auxiliary"), fn.string("auxiliary"), node)
    return expression.compile()
