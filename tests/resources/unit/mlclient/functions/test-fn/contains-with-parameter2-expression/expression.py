from mlclient.functions.xqy import cts, fn


def run():
    return fn.contains("parameter1", fn.string(cts.search().index(1))).compile()
