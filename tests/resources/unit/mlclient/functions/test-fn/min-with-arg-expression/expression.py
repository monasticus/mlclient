from mlclient.functions.xqy import cts, fn


def run():
    return fn.min(fn.count(cts.search().index(1))).compile()
