from mlclient.xquery import fn


def run():
    return fn.concat(2, "parameters").compile()
