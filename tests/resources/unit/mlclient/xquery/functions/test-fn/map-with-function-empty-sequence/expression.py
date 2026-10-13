from mlclient.xquery import cts, fn


def run():
    return fn.map(None, cts.search().pos(1)).compile()
