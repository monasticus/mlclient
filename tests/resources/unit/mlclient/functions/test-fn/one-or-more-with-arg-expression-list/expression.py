from mlclient.functions.xqy import cts, fn


def run():
    return fn.one_or_more([cts.search().index(1), cts.search().index(2)]).compile()
