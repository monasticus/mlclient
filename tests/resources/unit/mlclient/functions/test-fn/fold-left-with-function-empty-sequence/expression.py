from mlclient.functions.xqy import cts, fn


def run():
    return fn.fold_left(None, cts.search().index(1), cts.search().index(1)).compile()
