from mlclient.functions.xqy import cts, fn


def run():
    return fn.trace(cts.search().index(1), fn.string(cts.search().index(1))).compile()
