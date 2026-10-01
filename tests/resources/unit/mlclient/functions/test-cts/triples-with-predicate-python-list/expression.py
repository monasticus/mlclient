from mlclient.functions.xqy import cts


def run():
    return cts.triples(predicate=["predicate", 123, 2.5, True]).compile()
