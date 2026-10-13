from mlclient.xquery import fn


def run():
    return fn.collection(["/products/1.xml"]).compile()
