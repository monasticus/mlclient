from mlclient.functions.xqy import cts, fn


def run():
    return fn.string_join(fn.string(cts.search().index(1)), "parameter2").compile()
