from mlclient.xquery import cts, fn


def run():
    return cts.percentile(fn.count(cts.search().pos(1)), 2.5).compile()
