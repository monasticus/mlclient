from mlclient.xquery import cts, fn


def run():
    return fn.index_of(
        [cts.search().pos(1), cts.search().pos(2)], "srch-param",
    ).compile()
