from mlclient.xquery import fn


def run():
    return fn.matches(None, "logic").compile()
