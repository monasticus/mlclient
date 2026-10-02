from mlclient.functions.xqy import cts


def run():
    return cts.train(set(), cts.search().pos(1))
