from mlclient.xquery import cts, fn


def run():
    return fn.round_half_to_even(fn.count(cts.search().pos(1))).compile()
