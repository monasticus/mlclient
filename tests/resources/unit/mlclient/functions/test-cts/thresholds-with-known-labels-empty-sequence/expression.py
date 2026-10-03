from mlclient.functions.xqy import cts


def run():
    return cts.thresholds(cts.search().pos(1), None).compile()
