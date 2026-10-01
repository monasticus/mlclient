from mlclient.functions.xqy import cts, fn


def run():
    return fn.qname(fn.string(cts.search().index(1)), "p:item").compile()
