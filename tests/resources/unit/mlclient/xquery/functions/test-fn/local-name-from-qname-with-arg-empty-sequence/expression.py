from mlclient.xquery import fn


def run():
    return fn.local_name_from_qname(None).compile()
