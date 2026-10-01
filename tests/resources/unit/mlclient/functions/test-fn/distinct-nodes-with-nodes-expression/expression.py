from mlclient.functions.xqy import cts, fn


def run():
    return fn.distinct_nodes(cts.search().index(1)).compile()
