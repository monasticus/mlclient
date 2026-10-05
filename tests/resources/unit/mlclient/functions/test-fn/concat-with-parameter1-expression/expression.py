from mlclient.functions.xqy import cts, fn


def run():
    return fn.concat(fn.count(cts.search().pos(1)), "parameters").compile()
