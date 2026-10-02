from mlclient.functions.xqy import cts, fn


def run():
    return fn.index_of(fn.count(cts.search().pos(1)), "srch-param").compile()
