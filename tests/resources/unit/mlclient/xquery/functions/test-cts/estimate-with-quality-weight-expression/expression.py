from mlclient.xquery import cts, fn


def run():
    return cts.estimate(quality_weight=fn.count(cts.search().pos(1))).compile()
