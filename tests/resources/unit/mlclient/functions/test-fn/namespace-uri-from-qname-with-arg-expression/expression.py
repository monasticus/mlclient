from mlclient.functions.xqy import fn


def run():
    return fn.namespace_uri_from_qname(
        fn.qname("https://example.com/products", "p:item"),
    ).compile()
