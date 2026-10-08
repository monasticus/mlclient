from mlclient.xquery import cts, fn


def run():
    return cts.collections(forest_ids=fn.count(cts.search().pos(1))).compile()
