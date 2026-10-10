from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_range_query(
        [
            fn.qname("https://example.com/products", "p:item"),
            fn.qname("https://example.com/products", "p:item"),
        ],
        "id",
        "=",
        "value",
    ).compile()
