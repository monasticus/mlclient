from mlclient.xquery import cts, fn


def run():
    return cts.search(options=fn.string(cts.search().pos(1))).compile()
