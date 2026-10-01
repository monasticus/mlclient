from mlclient.functions.xqy import cts, fn


def run():
    return fn.substring_before(fn.string(cts.search().index(1)), "needle").compile()
