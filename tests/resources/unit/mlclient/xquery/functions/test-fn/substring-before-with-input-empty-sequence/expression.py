from mlclient.xquery import fn


def run():
    return fn.substring_before(None, "needle").compile()
