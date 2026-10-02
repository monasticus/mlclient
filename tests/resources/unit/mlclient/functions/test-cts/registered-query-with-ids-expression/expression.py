from mlclient.functions.xqy import cts, fn


def run():
    return cts.registered_query(fn.count(cts.search().pos(1))).compile()
