from mlclient.xquery import fn


def run():
    return fn.max(True).compile()
