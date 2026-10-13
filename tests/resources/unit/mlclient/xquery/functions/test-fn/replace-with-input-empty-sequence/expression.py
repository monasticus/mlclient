from mlclient.xquery import fn


def run():
    return fn.replace(None, "logic", "database").compile()
