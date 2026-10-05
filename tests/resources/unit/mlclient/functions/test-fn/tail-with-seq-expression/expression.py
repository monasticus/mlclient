from mlclient.functions.xqy import cts, fn


def run():
    return fn.tail(cts.search().pos(1)).compile()
