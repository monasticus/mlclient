from mlclient.functions.xqy import cts, fn


def run():
    return fn.remove(cts.search().pos(1), fn.count(cts.search().pos(1))).compile()
