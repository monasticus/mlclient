from mlclient.xquery import cts, fn


def run():
    return cts.uris(quality_weight=fn.count(cts.search().pos(1))).compile()
