from mlclient.xquery import fn


def run():
    return fn.floor(2.5).compile()
