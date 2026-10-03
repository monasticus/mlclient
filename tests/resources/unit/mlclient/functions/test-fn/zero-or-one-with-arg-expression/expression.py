from mlclient.functions.xqy import cts, fn


def run():
    return fn.zero_or_one(cts.search().pos(1)).compile()
