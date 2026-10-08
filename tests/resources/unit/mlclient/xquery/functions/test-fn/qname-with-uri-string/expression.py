from mlclient.xquery import fn


def run():
    return fn.qname("/products/1.xml", "p:item").compile()
