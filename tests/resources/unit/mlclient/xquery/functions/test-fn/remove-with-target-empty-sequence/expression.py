from mlclient.xquery import fn


def run():
    return fn.remove(None, 2).compile()
