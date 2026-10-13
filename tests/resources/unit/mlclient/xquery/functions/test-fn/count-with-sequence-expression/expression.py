from mlclient.xquery import cts, fn


def run():
    return fn.count(cts.search().pos(1)).compile()
