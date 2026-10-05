from mlclient.functions.xqy import cts


def run():
    return cts.triples(subject=True).compile()
