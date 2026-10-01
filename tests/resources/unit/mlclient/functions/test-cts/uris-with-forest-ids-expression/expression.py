from mlclient.functions.xqy import cts, fn


def run():
    return cts.uris(forest_ids=fn.count(cts.search().index(1))).compile()
