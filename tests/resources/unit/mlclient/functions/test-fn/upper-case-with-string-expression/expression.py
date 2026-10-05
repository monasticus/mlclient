from mlclient.functions.xqy import cts, fn


def run():
    return fn.upper_case(fn.string(cts.search().pos(1))).compile()
