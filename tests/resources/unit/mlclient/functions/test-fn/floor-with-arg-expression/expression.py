from mlclient.functions.xqy import cts, fn


def run():
    return fn.floor(fn.count(cts.search().pos(1))).compile()
