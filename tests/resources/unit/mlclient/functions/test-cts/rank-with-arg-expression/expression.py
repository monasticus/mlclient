from mlclient.functions.xqy import cts, fn


def run():
    return cts.rank(fn.count(cts.search().index(1)), "value").compile()
