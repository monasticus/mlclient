from mlclient.functions.xqy import cts, fn


def run():
    return fn.compare(fn.string(cts.search().index(1)), "comparand2").compile()
