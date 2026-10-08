from mlclient.xquery import cts, fn


def run():
    return cts.point(10.0, fn.count(cts.search().pos(1))).compile()
