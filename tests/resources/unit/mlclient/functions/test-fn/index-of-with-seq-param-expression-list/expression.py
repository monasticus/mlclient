from mlclient.functions.xqy import cts, fn


def run():
    return fn.index_of(
        [cts.search().index(1), cts.search().index(2)], "srch-param",
    ).compile()
