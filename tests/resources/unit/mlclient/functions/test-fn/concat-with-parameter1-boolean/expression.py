from mlclient.functions.xqy import fn


def run():
    return fn.concat(True, "parameters").compile()
