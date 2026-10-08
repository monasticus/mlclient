from mlclient.xquery import cts, fn


def run():
    return cts.median(fn.count(cts.search().pos(1))).compile()
