from mlclient.functions.xqy import cts


def run():
    return cts.thresholds(None, cts.search().index(1)).compile()
