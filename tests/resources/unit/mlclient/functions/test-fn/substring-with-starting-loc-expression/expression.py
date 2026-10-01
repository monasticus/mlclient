from mlclient.functions.xqy import cts, fn


def run():
    return fn.substring("source-string", fn.count(cts.search().index(1))).compile()
