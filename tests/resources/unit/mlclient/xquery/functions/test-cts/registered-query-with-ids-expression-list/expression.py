from mlclient.xquery import cts, fn


def run():
    return cts.registered_query(
        [fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
