from mlclient.functions.xqy import cts, fn


def run():
    return cts.uris(start=fn.string(cts.search().index(1))).compile()
