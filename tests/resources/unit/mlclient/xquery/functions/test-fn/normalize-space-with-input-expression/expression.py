from mlclient.xquery import cts, fn


def run():
    return fn.normalize_space(fn.string(cts.search().pos(1))).compile()
