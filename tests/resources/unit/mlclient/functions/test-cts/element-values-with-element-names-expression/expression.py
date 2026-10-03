from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_values(
        fn.qname("https://example.com/products", "p:item"),
    ).compile()
