from mlclient.xquery import cts, fn


def run():
    return cts.element_value_geospatial_co_occurrences(
        fn.qname("https://example.com/products", "p:item"), "item",
    ).compile()
