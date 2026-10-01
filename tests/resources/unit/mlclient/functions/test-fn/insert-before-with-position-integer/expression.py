from mlclient.functions.xqy import cts, fn


def run():
    return fn.insert_before(cts.search().index(1), 2, cts.search().index(1)).compile()
