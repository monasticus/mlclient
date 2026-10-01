from mlclient.functions.xqy import cts, fn, xs


def run():
    return xs.integer(fn.count(cts.search().index(1))).compile()
