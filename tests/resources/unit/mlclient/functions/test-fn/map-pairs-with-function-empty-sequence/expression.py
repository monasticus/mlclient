from mlclient.functions.xqy import cts, fn


def run():
    return fn.map_pairs(None, cts.search().pos(1), cts.search().pos(1)).compile()
