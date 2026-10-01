from mlclient.functions.xqy import cts, fn


def run():
    return fn.deep_equal(cts.search().index(1), cts.search().index(1)).compile()
