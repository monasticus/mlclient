from mlclient.xquery import cts, fn


def run():
    return fn.reverse(cts.search().pos(1)).compile()
