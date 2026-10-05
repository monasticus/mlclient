from mlclient.functions.xqy import cts, fn


def run():
    return fn.ends_with("parameter1", fn.string(cts.search().pos(1))).compile()
