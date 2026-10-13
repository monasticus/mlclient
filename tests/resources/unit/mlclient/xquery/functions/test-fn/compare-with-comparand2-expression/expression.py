from mlclient.xquery import cts, fn


def run():
    return fn.compare("comparand1", fn.string(cts.search().pos(1))).compile()
