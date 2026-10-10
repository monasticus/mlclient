from mlclient.xquery import cts, fn


def run():
    return fn.round(fn.count(cts.search().pos(1))).compile()
