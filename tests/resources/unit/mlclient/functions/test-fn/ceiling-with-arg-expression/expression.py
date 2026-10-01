from mlclient.functions.xqy import cts, fn


def run():
    return fn.ceiling(fn.count(cts.search().index(1))).compile()
