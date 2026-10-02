from mlclient.functions.xqy import cts, fn


def run():
    return fn.data(cts.search().pos(1)).compile()
