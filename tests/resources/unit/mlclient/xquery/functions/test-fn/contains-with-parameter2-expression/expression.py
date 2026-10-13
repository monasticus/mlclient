from mlclient.xquery import cts, fn


def run():
    return fn.contains("parameter1", fn.string(cts.search().pos(1))).compile()
