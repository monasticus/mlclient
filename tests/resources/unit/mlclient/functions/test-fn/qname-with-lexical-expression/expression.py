from mlclient.functions.xqy import cts, fn


def run():
    return fn.qname("/products/1.xml", fn.string(cts.search().pos(1))).compile()
