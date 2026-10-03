from mlclient.functions.xqy import cts, fn


def run():
    return fn.unordered(cts.search().pos(1)).compile()
