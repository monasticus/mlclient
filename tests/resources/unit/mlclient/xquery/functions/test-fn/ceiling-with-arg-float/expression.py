from mlclient.xquery import fn


def run():
    return fn.ceiling(2.5).compile()
