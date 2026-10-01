from mlclient.functions.xqy import cts, fn


def run():
    return fn.concat(fn.count(cts.search().index(1)), "parameters").compile()
