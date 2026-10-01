from mlclient.functions.xqy import cts, fn


def run():
    return fn.tail(cts.search().index(1)).compile()
