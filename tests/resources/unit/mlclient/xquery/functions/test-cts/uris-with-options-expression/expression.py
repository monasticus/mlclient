from mlclient.xquery import cts, fn


def run():
    return cts.uris(options=fn.string(cts.search().pos(1))).compile()
