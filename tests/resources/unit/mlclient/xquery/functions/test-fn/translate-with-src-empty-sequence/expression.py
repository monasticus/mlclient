from mlclient.xquery import fn


def run():
    return fn.translate(None, "abc", "ABC").compile()
