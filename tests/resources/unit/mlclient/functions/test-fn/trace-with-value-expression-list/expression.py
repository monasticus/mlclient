from mlclient.functions.xqy import cts, fn


def run():
    return fn.trace(
        [cts.search().index(1), cts.search().index(2)], "trace-label",
    ).compile()
