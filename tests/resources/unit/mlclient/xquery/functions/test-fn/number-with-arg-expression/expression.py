from mlclient.xquery import cts, fn


def run():
    return fn.number(fn.count(cts.search().pos(1))).compile()
