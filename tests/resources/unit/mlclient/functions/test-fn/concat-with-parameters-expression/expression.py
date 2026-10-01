from mlclient.functions.xqy import cts, fn


def run():
    return fn.concat("parameter1", fn.count(cts.search().index(1))).compile()
