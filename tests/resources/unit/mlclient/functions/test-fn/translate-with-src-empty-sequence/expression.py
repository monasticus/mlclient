from mlclient.functions.xqy import fn


def run():
    return fn.translate(None, "abc", "ABC").compile()
