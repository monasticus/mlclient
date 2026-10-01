from mlclient.functions.xqy import cts, fn


def run():
    return cts.registered_query(123, options=fn.string(cts.search().index(1))).compile()
