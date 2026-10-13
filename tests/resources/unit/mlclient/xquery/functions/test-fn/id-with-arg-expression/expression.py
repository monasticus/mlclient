from mlclient.xquery import cts, fn


def run():
    return fn.id(fn.string(cts.search().pos(1))).compile()
