from mlclient.functions.xqy import fn


def run():
    return fn.local_name_from_qname(
        fn.qname("https://example.com/products", "p:item"),
    ).compile()
