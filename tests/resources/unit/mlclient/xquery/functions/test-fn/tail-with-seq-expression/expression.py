from mlclient.xquery import cts, fn


def run():
    return fn.tail(cts.search().pos(1)).compile()
