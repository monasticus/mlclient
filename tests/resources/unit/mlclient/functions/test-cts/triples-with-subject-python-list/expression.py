from mlclient.functions.xqy import cts


def run():
    return cts.triples(subject=["subject", 123, 2.5, True]).compile()
