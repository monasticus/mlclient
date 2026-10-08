from mlclient.xquery import cts


def run():
    return cts.triples(predicate=2.5).compile()
