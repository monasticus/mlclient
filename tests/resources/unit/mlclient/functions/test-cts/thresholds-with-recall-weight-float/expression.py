from mlclient.functions.xqy import cts


def run():
    return cts.thresholds(
        cts.search().index(1), cts.search().index(1), recall_weight=2.5,
    ).compile()
