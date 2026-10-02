from mlclient.functions.xqy import cts, fn


def run():
    return fn.map_pairs(object(), cts.search().pos(1), cts.search().pos(1))
