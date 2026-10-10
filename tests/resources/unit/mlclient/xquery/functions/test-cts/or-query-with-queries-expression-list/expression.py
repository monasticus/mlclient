from mlclient.xquery import cts, fn


def run():
    return cts.or_query(
        [fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
