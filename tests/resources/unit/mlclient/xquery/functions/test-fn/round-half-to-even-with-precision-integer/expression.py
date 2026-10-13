from mlclient.xquery import fn


def run():
    return fn.round_half_to_even(2.5, precision=2).compile()
