from mlclient.functions.xqy import cts, fn


def run():
    return cts.triples(subject=fn.count(cts.search().index(1))).compile()
