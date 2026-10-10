from mlclient.xquery import cts, fn


def run():
    return cts.uris(forest_ids=fn.count(cts.search().pos(1))).compile()
