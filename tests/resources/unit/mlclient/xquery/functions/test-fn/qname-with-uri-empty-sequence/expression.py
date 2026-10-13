from mlclient.xquery import fn


def run():
    return fn.qname(None, "p:item").compile()
