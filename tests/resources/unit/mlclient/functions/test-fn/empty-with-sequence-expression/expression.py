from mlclient.functions.xqy import cts, fn


def run():
    return fn.empty(cts.search().pos(1)).compile()
