from mlclient.functions.xqy import fn


def run():
    return fn.substring("source-string", 2.5, length=2.5).compile()
