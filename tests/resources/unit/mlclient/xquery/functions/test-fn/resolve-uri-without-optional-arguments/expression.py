from mlclient.xquery import fn


def run():
    return fn.resolve_uri("items/1.xml").compile()
