from mlclient.xquery import cts


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.relevance_info(node=node)
    return expression.compile()
