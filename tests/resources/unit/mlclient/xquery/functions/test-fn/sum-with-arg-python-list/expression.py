from mlclient.xquery import fn


def run():
    return fn.sum(["arg", 2, 2.5, True]).compile()
