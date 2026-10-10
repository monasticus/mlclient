from mlclient.xquery import fn


def run():
    return fn.resolve_uri(None).compile()
