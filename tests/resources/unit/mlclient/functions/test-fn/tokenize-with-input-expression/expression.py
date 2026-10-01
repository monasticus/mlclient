from mlclient.functions.xqy import cts, fn


def run():
    return fn.tokenize(fn.string(cts.search().index(1)), "logic").compile()
