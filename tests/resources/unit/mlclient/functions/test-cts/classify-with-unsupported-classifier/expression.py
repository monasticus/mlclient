from mlclient.functions.xqy import cts


def run():
    return cts.classify(cts.search().index(1), set())
