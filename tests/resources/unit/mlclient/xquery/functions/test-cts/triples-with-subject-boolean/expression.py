from mlclient.xquery import cts


def run():
    return cts.triples(subject=True).compile()
