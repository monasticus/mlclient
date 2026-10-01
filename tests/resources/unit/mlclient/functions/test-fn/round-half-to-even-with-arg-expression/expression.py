from mlclient.functions.xqy import cts, fn


def run():
    return fn.round_half_to_even(fn.count(cts.search().index(1))).compile()
