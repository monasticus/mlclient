from mlclient.xquery import fn


def run():
    return fn.concat(2.5, "parameters").compile()
