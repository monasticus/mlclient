from mlclient.functions.xqy import cts, fn


def run():
    return cts.triples(predicate=fn.count(cts.search().pos(1))).compile()
