from mlclient.xquery import cts, fn


def run():
    return cts.linestring(fn.string(cts.search().pos(1))).compile()
