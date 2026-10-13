from mlclient.xquery import fn


def run():
    return fn.count(None).compile()
