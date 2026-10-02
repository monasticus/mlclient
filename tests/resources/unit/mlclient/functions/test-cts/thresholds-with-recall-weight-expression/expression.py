from mlclient.functions.xqy import cts, fn


def run():
    return cts.thresholds(
        cts.search().pos(1),
        cts.search().pos(1),
        recall_weight=fn.count(cts.search().pos(1)),
    ).compile()
