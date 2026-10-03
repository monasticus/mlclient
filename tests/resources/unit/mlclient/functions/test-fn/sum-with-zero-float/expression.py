from mlclient.functions.xqy import fn


def run():
    return fn.sum("arg", zero=2.5).compile()
