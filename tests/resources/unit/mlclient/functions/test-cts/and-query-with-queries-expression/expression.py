from mlclient.functions.xqy import cts, fn


def run():
    return cts.and_query(fn.string(cts.search().pos(1))).compile()
