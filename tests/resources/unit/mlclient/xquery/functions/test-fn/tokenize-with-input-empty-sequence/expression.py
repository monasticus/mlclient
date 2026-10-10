from mlclient.xquery import fn


def run():
    return fn.tokenize(None, "logic").compile()
