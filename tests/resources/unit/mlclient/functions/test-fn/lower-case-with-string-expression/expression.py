from mlclient.functions.xqy import cts, fn


def run():
    return fn.lower_case(fn.string(cts.search().index(1))).compile()
