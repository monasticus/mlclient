from mlclient.xquery import cts, fn


def run():
    return cts.triples(operator=fn.string(cts.search().pos(1))).compile()
