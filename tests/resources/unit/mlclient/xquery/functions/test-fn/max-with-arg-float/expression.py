from mlclient.xquery import fn


def run():
    return fn.max(2.5).compile()
