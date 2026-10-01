from mlclient.functions.xqy import cts, fn


def run():
    return fn.fold_left(object(), cts.search().index(1), cts.search().index(1))
