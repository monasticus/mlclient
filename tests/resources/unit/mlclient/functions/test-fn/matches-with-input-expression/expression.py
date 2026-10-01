from mlclient.functions.xqy import cts, fn


def run():
    return fn.matches(fn.string(cts.search().index(1)), "logic").compile()
