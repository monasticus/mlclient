from mlclient.functions.xqy import cts, fn


def run():
    return cts.circle(fn.count(cts.search().index(1)), cts.point(10, 20)).compile()
