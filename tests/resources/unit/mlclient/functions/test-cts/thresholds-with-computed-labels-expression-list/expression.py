from mlclient.functions.xqy import cts


def run():
    return cts.thresholds(
        [cts.search().index(1), cts.search().index(2)], cts.search().index(1),
    ).compile()
