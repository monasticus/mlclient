from mlclient.functions.xqy import cts, fn


def run():
    return fn.exists(cts.search().index(1)).compile()
