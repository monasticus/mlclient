from mlclient.xquery import fn


def run():
    return fn.exists(None).compile()
