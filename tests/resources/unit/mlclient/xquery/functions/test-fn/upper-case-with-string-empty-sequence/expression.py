from mlclient.xquery import fn


def run():
    return fn.upper_case(None).compile()
