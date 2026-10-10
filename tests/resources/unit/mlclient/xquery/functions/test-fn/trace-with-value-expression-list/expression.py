from mlclient.xquery import cts, fn


def run():
    return fn.trace(
        [cts.search().pos(1), cts.search().pos(2)], "trace-label",
    ).compile()
