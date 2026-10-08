from mlclient.xquery import fn


def run():
    return fn.idref(["arg"]).compile()
