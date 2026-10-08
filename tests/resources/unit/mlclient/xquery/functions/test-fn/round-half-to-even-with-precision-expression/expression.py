from mlclient.xquery import cts, fn


def run():
    return fn.round_half_to_even(
        2.5, precision=fn.count(cts.search().pos(1)),
    ).compile()
