from mlclient.functions.xqy import cts, fn


def run():
    return fn.system_property(fn.string(cts.search().pos(1))).compile()
