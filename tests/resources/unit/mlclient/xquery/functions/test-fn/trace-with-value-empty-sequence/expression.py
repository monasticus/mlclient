from mlclient.xquery import fn


def run():
    return fn.trace(None, "trace-label").compile()
