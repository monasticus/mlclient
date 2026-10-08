from mlclient.xquery import cts


def run():
    return cts.thresholds(
        cts.search().pos(1), cts.search().pos(1), recall_weight=2.5,
    ).compile()
