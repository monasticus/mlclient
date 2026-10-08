from mlclient.xquery import fn


def run():
    return fn.doc_available(None).compile()
