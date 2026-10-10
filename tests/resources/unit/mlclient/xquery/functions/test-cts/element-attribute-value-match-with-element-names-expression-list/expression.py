from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_value_match(
        [
            fn.qname("https://example.com/products", "p:item"),
            fn.qname("https://example.com/products", "p:item"),
        ],
        "id",
        "prod*",
    ).compile()
