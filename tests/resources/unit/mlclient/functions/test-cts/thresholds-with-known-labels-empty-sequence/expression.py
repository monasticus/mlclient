from mlclient.functions.xqy import cts


def run():
    return cts.thresholds(cts.search().index(1), None).compile()
