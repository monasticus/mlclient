from mlclient.functions.xqy import cts, fn


def run():
    return cts.registered_query(
        [fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
