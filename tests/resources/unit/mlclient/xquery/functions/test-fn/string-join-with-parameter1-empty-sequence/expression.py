from mlclient.xquery import fn


def run():
    return fn.string_join(None, "parameter2").compile()
