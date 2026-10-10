from mlclient.xquery import cts


def run():
    return cts.triples(operator=None).compile()
