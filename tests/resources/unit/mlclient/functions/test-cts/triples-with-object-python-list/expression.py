from mlclient.functions.xqy import cts


def run():
    return cts.triples(object=["object", 123, 2.5, True]).compile()
