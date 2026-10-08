from mlclient.xquery import cts, fn


def run():
    return cts.path_reference(fn.string(cts.search().pos(1))).compile()
