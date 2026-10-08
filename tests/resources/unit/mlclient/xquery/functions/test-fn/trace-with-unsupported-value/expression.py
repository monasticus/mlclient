from mlclient.xquery import fn


def run():
    return fn.trace(object(), "trace-label")
