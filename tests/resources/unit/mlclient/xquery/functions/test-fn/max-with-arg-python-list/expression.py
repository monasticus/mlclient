from mlclient.xquery import fn


def run():
    return fn.max(["arg", 2, 2.5, True]).compile()
