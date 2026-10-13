from mlclient.xquery import cts, fn


def run():
    return cts.estimate(options=fn.string(cts.search().pos(1))).compile()
