from mlclient.functions.xqy import cts


def run():
    return cts.classify(cts.search().pos(1), set())
