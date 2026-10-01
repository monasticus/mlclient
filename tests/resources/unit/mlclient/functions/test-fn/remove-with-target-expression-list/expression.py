from mlclient.functions.xqy import cts, fn


def run():
    return fn.remove([cts.search().index(1), cts.search().index(2)], 2).compile()
