from mlclient.functions.xqy import cts, fn


def run():
    return cts.collections(quality_weight=fn.count(cts.search().pos(1))).compile()
