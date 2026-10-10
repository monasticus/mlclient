from mlclient.xquery import fn


def run():
    return fn.starts_with(None, "parameter2").compile()
