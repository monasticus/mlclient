from mlclient.xquery import cts, fn


def run():
    return fn.type_available(fn.string(cts.search().pos(1))).compile()
