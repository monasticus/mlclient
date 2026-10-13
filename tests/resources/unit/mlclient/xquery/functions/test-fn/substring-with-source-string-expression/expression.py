from mlclient.xquery import cts, fn


def run():
    return fn.substring(fn.string(cts.search().pos(1)), 2.5).compile()
