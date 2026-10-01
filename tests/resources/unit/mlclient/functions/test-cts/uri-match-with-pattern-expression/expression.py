from mlclient.functions.xqy import cts, fn


def run():
    return cts.uri_match(fn.string(cts.search().index(1))).compile()
