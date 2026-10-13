from mlclient.xquery import cts, fn


def run():
    return fn.idref(fn.string(cts.search().pos(1))).compile()
