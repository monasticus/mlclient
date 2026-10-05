from mlclient.functions.xqy import cts, fn


def run():
    return fn.one_or_more(cts.search().pos(1)).compile()
