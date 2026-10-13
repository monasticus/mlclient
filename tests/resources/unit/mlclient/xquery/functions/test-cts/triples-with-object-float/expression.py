from mlclient.xquery import cts


def run():
    return cts.triples(object=2.5).compile()
