from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.document(fn.string("auxiliary"), base_node=node)
    return expression.compile()
