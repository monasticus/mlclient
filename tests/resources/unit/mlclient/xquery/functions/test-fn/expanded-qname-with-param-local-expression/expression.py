from mlclient.xquery import cts, fn


def run():
    return fn.expanded_qname(
        "https://example.com/products", fn.string(cts.search().pos(1)),
    ).compile()
