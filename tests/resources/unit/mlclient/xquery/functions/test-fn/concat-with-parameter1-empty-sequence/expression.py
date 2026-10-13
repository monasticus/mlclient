from mlclient.xquery import fn


def run():
    return fn.concat(None, "parameters").compile()
