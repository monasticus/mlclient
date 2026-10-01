from mlclient.functions.xqy import cts


def run():
    return cts.train(None, cts.search().index(1)).compile()
