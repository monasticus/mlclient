from mlclient.xquery import cts, fn


def run():
    return cts.registered_query(123, options=fn.string(cts.search().pos(1))).compile()
