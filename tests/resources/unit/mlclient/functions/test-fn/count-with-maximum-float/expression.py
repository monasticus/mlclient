from mlclient.functions.xqy import cts, fn


def run():
    return fn.count(cts.search().pos(1), maximum=2.5).compile()
