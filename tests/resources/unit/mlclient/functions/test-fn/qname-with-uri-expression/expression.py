from mlclient.functions.xqy import cts, fn


def run():
    return fn.qname(fn.string(cts.search().pos(1)), "p:item").compile()
