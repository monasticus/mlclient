from mlclient.xquery import fn


def run():
    return fn.sum("arg", zero="zero").compile()
