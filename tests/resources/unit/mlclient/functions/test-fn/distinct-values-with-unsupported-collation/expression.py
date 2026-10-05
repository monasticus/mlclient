from mlclient.functions.xqy import cts, fn


def run():
    return fn.distinct_values(cts.search().pos(1), collation=object())
