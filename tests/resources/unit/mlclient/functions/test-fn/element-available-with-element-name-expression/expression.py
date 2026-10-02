from mlclient.functions.xqy import cts, fn


def run():
    return fn.element_available(fn.string(cts.search().pos(1))).compile()
