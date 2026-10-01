from mlclient.functions.xqy import cts, fn


def run():
    return cts.percentile(fn.count(cts.search().index(1)), 2.5).compile()
