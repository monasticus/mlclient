from mlclient.functions.xqy import cts, fn


def run():
    return fn.substring("source-string", fn.count(cts.search().pos(1))).compile()
