from mlclient.xquery import cts, fn


def run():
    return cts.percentile(
        2.5, [fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
