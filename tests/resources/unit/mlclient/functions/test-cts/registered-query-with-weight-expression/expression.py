from mlclient.functions.xqy import cts, fn


def run():
    return cts.registered_query(123, weight=fn.count(cts.search().pos(1))).compile()
