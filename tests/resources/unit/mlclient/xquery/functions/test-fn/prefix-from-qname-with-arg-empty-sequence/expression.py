from mlclient.xquery import fn


def run():
    return fn.prefix_from_qname(None).compile()
