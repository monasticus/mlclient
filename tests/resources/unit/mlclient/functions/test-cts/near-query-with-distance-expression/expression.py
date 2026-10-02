from mlclient.functions.xqy import cts, fn


def run():
    return cts.near_query("queries", distance=fn.count(cts.search().pos(1))).compile()
