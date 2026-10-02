from mlclient.functions.xqy import cts, fn


def run():
    return fn.expanded_qname(fn.string(cts.search().pos(1)), "item").compile()
