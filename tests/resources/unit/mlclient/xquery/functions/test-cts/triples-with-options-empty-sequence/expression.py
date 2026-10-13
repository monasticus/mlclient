from mlclient.xquery import cts


def run():
    return cts.triples(options=None).compile()
