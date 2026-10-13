from mlclient.xquery import fn


def run():
    return fn.min(True).compile()
