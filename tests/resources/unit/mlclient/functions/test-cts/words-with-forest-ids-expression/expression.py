from mlclient.functions.xqy import cts, fn


def run():
    return cts.words(forest_ids=fn.count(cts.search().pos(1))).compile()
