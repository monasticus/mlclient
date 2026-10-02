from mlclient.functions.xqy import cts, fn


def run():
    return cts.percentile(
        [fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))], 2.5,
    ).compile()
