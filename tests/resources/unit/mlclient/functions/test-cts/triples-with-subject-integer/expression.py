from mlclient.functions.xqy import cts


def run():
    return cts.triples(subject=123).compile()
