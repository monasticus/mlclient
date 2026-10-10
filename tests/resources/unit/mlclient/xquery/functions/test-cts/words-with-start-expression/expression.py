from mlclient.xquery import cts, fn


def run():
    return cts.words(start=fn.string(cts.search().pos(1))).compile()
