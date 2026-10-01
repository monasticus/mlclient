from mlclient.functions.xqy import fn


def run():
    return fn.doc("/products/1.xml").compile()
