from mlclient.functions.xqy import cts, fn


def run():
    return cts.quality_order(options=fn.string(cts.search().index(1))).compile()
