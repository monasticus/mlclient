from mlclient.xquery import fn


def run():
    return fn.contains(None, "parameter2").compile()
