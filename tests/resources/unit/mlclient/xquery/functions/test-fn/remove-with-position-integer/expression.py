from mlclient.xquery import cts, fn


def run():
    return fn.remove(cts.search().pos(1), 2).compile()
