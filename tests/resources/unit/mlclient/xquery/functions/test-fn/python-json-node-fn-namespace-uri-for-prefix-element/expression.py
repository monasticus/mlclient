from mlclient.xquery import fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = fn.namespace_uri_for_prefix(fn.string("auxiliary"), node)
    return expression.compile()
