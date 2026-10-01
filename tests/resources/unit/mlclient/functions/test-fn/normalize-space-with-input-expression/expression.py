from mlclient.functions.xqy import cts, fn


def run():
    return fn.normalize_space(fn.string(cts.search().index(1))).compile()
