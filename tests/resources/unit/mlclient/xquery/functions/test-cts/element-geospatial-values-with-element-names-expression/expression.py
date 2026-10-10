from mlclient.xquery import cts, fn


def run():
    return cts.element_geospatial_values(
        fn.qname("https://example.com/products", "p:item"),
    ).compile()
