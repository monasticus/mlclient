from mlclient.functions.xqy import cts


def run():
    return cts.train(set(), cts.search().index(1))
