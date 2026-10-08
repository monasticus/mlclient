from mlclient.xquery import cts, fn


def run():
    return fn.insert_before(None, 2, cts.search().pos(1)).compile()
