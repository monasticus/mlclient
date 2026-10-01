from mlclient.functions.xqy import cts, fn


def run():
    return fn.count(cts.search().index(1), maximum=2.5).compile()
