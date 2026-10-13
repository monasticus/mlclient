from mlclient.xquery import fn


def run():
    return fn.substring(None, 2.5).compile()
