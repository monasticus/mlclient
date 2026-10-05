from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_value_ranges(
        [
            fn.qname("https://example.com/products", "p:item"),
            fn.qname("https://example.com/products", "p:item"),
        ],
    ).compile()
