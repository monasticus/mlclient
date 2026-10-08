from mlclient.xquery import cts, fn


def run():
    return fn.distinct_values([cts.search().pos(1), cts.search().pos(2)]).compile()
