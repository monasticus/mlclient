from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_values(
        "item", fn.qname("https://example.com/products", "p:item"),
    ).compile()
