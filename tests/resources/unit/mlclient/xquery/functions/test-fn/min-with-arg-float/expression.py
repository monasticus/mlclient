from mlclient.xquery import fn


def run():
    return fn.min(2.5).compile()
