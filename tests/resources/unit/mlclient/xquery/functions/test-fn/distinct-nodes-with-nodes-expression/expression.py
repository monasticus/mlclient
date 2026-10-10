from mlclient.xquery import cts, fn


def run():
    return fn.distinct_nodes(cts.search().pos(1)).compile()
