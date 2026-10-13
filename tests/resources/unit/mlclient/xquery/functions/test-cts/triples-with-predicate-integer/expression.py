from mlclient.xquery import cts


def run():
    return cts.triples(predicate=123).compile()
