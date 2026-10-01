from mlclient.functions.xqy import cts, fn


def run():
    return fn.substring(fn.string(cts.search().index(1)), 2.5).compile()
