from mlclient.functions.xqy import cts, fn


def run():
    return fn.string_join("parameter1", fn.string(cts.search().pos(1))).compile()
