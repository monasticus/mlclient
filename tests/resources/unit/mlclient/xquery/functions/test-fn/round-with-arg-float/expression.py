from mlclient.xquery import fn


def run():
    return fn.round(2.5).compile()
