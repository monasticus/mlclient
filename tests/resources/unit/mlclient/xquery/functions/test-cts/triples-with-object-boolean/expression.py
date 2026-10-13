from mlclient.xquery import cts


def run():
    return cts.triples(object=True).compile()
