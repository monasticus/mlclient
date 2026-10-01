from mlclient.functions.xqy import cts


def run():
    return cts.thresholds(set(), cts.search().index(1))
