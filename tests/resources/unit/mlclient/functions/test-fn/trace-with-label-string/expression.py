from mlclient.functions.xqy import cts, fn


def run():
    return fn.trace(cts.search().index(1), "trace-label").compile()
