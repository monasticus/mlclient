from mlclient.functions.xqy import cts, fn


def run():
    return fn.exists(cts.search().pos(1)).compile()
