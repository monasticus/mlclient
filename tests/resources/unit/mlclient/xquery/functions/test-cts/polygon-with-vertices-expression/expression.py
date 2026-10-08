from mlclient.xquery import cts, fn


def run():
    return cts.polygon(fn.string(cts.search().pos(1))).compile()
