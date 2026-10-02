from mlclient.functions.xqy import cts, fn


def run():
    return fn.lower_case(fn.string(cts.search().pos(1))).compile()
