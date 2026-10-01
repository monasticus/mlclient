from mlclient.functions.xqy import cts, fn


def run():
    return fn.insert_before(object(), 2, cts.search().index(1))
