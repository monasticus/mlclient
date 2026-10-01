from mlclient.functions.xqy import cts, fn


def run():
    return fn.round_half_to_even(
        2.5, precision=fn.count(cts.search().index(1)),
    ).compile()
