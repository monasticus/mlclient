from mlclient.functions.xqy import cts, fn


def run():
    return fn.map(object(), cts.search().pos(1))
