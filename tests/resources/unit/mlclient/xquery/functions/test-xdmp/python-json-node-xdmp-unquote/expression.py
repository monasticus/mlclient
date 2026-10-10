from mlclient.xquery import xdmp


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = xdmp.unquote(node)
    return expression.compile()
