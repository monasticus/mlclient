from mlclient.functions.xqy import cts, fn


def run():
    return fn.compare("comparand1", fn.string(cts.search().index(1))).compile()
