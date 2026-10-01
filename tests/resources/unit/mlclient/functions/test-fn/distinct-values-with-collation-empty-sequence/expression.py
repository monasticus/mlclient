from mlclient.functions.xqy import cts, fn


def run():
    return fn.distinct_values(cts.search().index(1), collation=None).compile()
