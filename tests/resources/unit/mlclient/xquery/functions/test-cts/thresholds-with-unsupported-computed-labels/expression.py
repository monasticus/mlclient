from mlclient.xquery import cts


def run():
    return cts.thresholds(set(), cts.search().pos(1))
