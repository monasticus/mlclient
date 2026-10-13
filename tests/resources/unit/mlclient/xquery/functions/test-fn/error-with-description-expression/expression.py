from mlclient.xquery import cts, fn


def run():
    return fn.error(fn.string(cts.search().pos(1))).compile()
