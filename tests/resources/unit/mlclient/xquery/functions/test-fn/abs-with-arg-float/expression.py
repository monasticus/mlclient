from mlclient.xquery import fn


def run():
    return fn.abs(2.5).compile()
