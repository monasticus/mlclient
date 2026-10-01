from mlclient.functions.xqy import cts, fn


def run():
    return cts.box(fn.count(cts.search().index(1)), 2.5, 2.5, 2.5).compile()
