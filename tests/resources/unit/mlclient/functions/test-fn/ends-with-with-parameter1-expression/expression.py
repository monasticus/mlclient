from mlclient.functions.xqy import cts, fn


def run():
    return fn.ends_with(fn.string(cts.search().index(1)), "parameter2").compile()
