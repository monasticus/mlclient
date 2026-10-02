from mlclient.functions.xqy import cts, fn


def run():
    return fn.translate(fn.string(cts.search().pos(1)), "abc", "ABC").compile()
