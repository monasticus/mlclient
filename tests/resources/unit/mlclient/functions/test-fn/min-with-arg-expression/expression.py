from mlclient.functions.xqy import cts, fn


def run():
    return fn.min(fn.count(cts.search().pos(1))).compile()
