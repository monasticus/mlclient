from mlclient.xquery import cts, fn


def run():
    return cts.quality_order(options=fn.string(cts.search().pos(1))).compile()
