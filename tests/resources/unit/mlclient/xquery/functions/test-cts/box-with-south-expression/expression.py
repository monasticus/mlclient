from mlclient.xquery import cts, fn


def run():
    return cts.box(fn.count(cts.search().pos(1)), 2.5, 2.5, 2.5).compile()
