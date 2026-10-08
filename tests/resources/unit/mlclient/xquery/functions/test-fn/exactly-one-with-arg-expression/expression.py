from mlclient.xquery import cts, fn


def run():
    return fn.exactly_one(cts.search().pos(1)).compile()
