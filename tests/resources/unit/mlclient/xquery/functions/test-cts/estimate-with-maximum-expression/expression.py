from mlclient.xquery import cts, fn


def run():
    return cts.estimate(maximum=fn.count(cts.search().pos(1))).compile()
