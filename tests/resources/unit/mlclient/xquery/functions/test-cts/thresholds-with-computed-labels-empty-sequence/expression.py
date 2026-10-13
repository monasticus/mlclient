from mlclient.xquery import cts


def run():
    return cts.thresholds(None, cts.search().pos(1)).compile()
