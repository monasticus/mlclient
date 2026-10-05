from mlclient.functions.xqy import fn


def run():
    return fn.expanded_qname(None, "item").compile()
