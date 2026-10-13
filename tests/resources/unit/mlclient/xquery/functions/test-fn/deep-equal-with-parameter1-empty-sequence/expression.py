from mlclient.xquery import cts, fn


def run():
    return fn.deep_equal(None, cts.search().pos(1)).compile()
