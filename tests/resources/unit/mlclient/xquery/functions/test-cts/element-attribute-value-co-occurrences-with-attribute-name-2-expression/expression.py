from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_value_co_occurrences(
        "item", "id", "item", fn.qname("https://example.com/products", "p:item"),
    ).compile()
