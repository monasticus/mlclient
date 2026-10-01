from mlclient.functions.xqy import cts, fn


def run():
    return fn.map_pairs(None, cts.search().index(1), cts.search().index(1)).compile()
