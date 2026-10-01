from mlclient.functions.xqy import cts, fn


def run():
    return fn.collection([cts.search().index(1), cts.search().index(2)]).compile()
