from mlclient.functions.xqy import cts, fn


def run():
    return fn.trace(cts.search().pos(1), object())
