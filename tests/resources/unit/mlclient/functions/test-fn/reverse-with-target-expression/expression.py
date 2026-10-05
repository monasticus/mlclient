from mlclient.functions.xqy import cts, fn


def run():
    return fn.reverse(cts.search().pos(1)).compile()
