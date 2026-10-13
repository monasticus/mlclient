from mlclient.xquery import cts, fn


def run():
    return fn.error(cts.search().pos(1), "message", cts.search().pos(1)).compile()
