from mlclient.xquery import fn


def run():
    return fn.round_half_to_even(None).compile()
