from mlclient.xquery import fn


def run():
    return fn.ends_with(None, "parameter2").compile()
