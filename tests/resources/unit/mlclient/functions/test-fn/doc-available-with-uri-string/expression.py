from mlclient.functions.xqy import fn


def run():
    return fn.doc_available("/products/1.xml").compile()
