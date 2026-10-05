from mlclient.functions.xqy import cts


def run():
    return cts.classify(set(), cts.train(cts.search().pos(1), cts.search().pos(2)))
