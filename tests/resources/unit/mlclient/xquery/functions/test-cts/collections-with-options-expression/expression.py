from mlclient.xquery import cts, fn


def run():
    return cts.collections(options=fn.string(cts.search().pos(1))).compile()
