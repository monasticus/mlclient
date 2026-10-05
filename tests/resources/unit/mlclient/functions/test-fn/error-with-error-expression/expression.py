from mlclient.functions.xqy import cts, fn


def run():
    return fn.error(cts.search().pos(1)).compile()
