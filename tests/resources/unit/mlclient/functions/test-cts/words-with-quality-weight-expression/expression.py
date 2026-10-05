from mlclient.functions.xqy import cts, fn


def run():
    return cts.words(quality_weight=fn.count(cts.search().pos(1))).compile()
