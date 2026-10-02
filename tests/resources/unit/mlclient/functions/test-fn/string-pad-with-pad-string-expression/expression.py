from mlclient.functions.xqy import cts, fn


def run():
    return fn.string_pad(fn.string(cts.search().pos(1)), 2).compile()
