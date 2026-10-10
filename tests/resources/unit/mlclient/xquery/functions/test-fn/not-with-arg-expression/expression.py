from mlclient.xquery import cts, fn


def run():
    return fn.not_(cts.search().pos(1)).compile()
