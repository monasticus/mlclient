from mlclient.functions.xqy import cts, fn


def run():
    return fn.string_pad(fn.string(cts.search().index(1)), 2).compile()
