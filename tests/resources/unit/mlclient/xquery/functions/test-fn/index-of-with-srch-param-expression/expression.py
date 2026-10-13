from mlclient.xquery import cts, fn


def run():
    return fn.index_of("seq-param", fn.count(cts.search().pos(1))).compile()
