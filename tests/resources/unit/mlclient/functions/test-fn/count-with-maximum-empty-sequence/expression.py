from mlclient.functions.xqy import cts, fn


def run():
    return fn.count(cts.search().pos(1), maximum=None).compile()
