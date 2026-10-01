from mlclient.functions.xqy import cts, fn


def run():
    return fn.deep_equal(object(), cts.search().index(1))
