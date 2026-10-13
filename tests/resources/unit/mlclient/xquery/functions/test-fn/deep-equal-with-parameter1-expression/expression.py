from mlclient.xquery import cts, fn


def run():
    return fn.deep_equal(cts.search().pos(1), cts.search().pos(1)).compile()
