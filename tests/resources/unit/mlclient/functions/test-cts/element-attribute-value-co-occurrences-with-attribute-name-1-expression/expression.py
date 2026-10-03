from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_value_co_occurrences(
        "item", fn.qname("https://example.com/products", "p:item"), "item", "id",
    ).compile()
