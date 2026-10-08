from mlclient.xquery import cts, fn


def run():
    return fn.concat(fn.count(cts.search().pos(1)), "parameters").compile()
