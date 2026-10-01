from mlclient.functions.xqy import cts, fn


def run():
    return fn.fold_right(object(), cts.search().index(1), cts.search().index(1))
