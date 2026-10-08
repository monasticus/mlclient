from mlclient.xquery import fn


def run():
    return fn.sum(2.5).compile()
