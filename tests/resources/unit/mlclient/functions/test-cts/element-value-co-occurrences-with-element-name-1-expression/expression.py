from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_value_co_occurrences(
        fn.qname("https://example.com/products", "p:item"), "item",
    ).compile()
