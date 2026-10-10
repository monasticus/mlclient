from mlclient.xquery import cts, fn


def run():
    return fn.sum("arg", zero=fn.count(cts.search().pos(1))).compile()
