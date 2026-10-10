from mlclient.xquery import cts, fn


def run():
    return fn.deep_equal(object(), cts.search().pos(1))
