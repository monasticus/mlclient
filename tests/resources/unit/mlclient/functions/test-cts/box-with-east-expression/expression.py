from mlclient.functions.xqy import cts, fn


def run():
    return cts.box(2.5, 2.5, 2.5, fn.count(cts.search().index(1))).compile()
