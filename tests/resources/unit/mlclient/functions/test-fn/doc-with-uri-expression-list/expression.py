from mlclient.functions.xqy import cts, fn


def run():
    return fn.doc([cts.search().pos(1), cts.search().pos(2)]).compile()
