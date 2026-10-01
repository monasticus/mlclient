from mlclient.functions.xqy import cts, fn


def run():
    return fn.collection(fn.string(cts.search().index(1))).compile()
