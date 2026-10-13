from mlclient.xquery import fn


def run():
    return fn.sum(None).compile()
