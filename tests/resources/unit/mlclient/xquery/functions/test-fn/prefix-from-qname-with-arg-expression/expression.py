from mlclient.xquery import fn


def run():
    return fn.prefix_from_qname(
        fn.qname("https://example.com/products", "p:item"),
    ).compile()
