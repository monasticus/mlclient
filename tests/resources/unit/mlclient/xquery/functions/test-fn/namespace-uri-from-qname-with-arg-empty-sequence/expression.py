from mlclient.xquery import fn


def run():
    return fn.namespace_uri_from_qname(None).compile()
