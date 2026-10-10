from mlclient.xquery import cts, fn


def run():
    return fn.floor(fn.count(cts.search().pos(1))).compile()
