from mlclient.xquery import fn


def run():
    return fn.concat(True, "parameters").compile()
