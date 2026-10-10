from mlclient.xquery import cts, fn, xs


def run():
    return xs.integer(fn.count(cts.search().pos(1))).compile()
