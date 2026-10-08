from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_value_geospatial_co_occurrences(
        "item", "id", fn.qname("https://example.com/products", "p:item"),
    ).compile()
