from mlclient.xquery import cts, fn


def run():
    return cts.uri_match(fn.string(cts.search().pos(1))).compile()
