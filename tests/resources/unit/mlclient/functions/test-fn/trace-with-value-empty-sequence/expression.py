from mlclient.functions.xqy import fn


def run():
    return fn.trace(None, "trace-label").compile()
