from mlclient.functions.xqy import cts


def run():
    return cts.triples(predicate="predicate").compile()
