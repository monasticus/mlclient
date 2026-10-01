from mlclient.functions.xqy import cts, fn


def run():
    return fn.remove(cts.search().index(1), fn.count(cts.search().index(1))).compile()
