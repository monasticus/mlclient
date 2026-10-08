from mlclient.xquery import cts, fn


def run():
    return cts.search(forest_ids=fn.count(cts.search().pos(1))).compile()
