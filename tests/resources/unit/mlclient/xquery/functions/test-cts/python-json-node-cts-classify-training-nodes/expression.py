from mlclient.xquery import cts, fn


def run():
    node = {"label": "blue", "nested": [{"count": 2}]}
    expression = cts.classify(
        fn.string("auxiliary"), fn.string("auxiliary"), training_nodes=node,
    )
    return expression.compile()
