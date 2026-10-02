from mlclient.functions.xqy import cts, fn


def run():
    return fn.key(fn.string(cts.search().pos(1)), "42").compile()
