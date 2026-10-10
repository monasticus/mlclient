from mlclient.xquery import cts


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.entity_dictionary(node)
    return expression.compile()
