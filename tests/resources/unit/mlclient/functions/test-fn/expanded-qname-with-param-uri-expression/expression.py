from mlclient.functions.xqy import cts, fn


def run():
    return fn.expanded_qname(fn.string(cts.search().index(1)), "item").compile()
