from mlclient.functions.xqy import cts


def run():
    return cts.train(cts.search().pos(1), set())
