from mlclient.functions.xqy import cts, fn


def run():
    return fn.fold_right(object(), cts.search().pos(1), cts.search().pos(1))
