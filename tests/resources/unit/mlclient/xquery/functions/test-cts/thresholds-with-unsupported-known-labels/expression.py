from mlclient.xquery import cts


def run():
    return cts.thresholds(cts.search().pos(1), set())
