from mlclient.functions.xqy import cts, fn


def run():
    return fn.translate(fn.string(cts.search().index(1)), "abc", "ABC").compile()
