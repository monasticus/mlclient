from mlclient.functions.xqy import cts, fn


def run():
    return cts.thresholds(
        cts.search().index(1),
        cts.search().index(1),
        recall_weight=fn.count(cts.search().index(1)),
    ).compile()
