from mlclient.xquery import cts


def run():
    return cts.triples(subject=2.5).compile()
