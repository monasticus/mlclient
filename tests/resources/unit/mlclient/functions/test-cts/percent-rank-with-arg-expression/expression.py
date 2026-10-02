from mlclient.functions.xqy import cts, fn


def run():
    return cts.percent_rank(fn.count(cts.search().pos(1)), "value").compile()
