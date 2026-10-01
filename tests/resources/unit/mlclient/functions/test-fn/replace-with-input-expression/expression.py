from mlclient.functions.xqy import cts, fn


def run():
    return fn.replace(fn.string(cts.search().index(1)), "logic", "database").compile()
