from mlclient.functions.xqy import cts, fn


def run():
    return fn.index_of("seq-param", fn.count(cts.search().index(1))).compile()
