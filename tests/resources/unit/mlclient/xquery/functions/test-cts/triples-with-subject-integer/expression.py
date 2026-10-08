from mlclient.xquery import cts


def run():
    return cts.triples(subject=123).compile()
