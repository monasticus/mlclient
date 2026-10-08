from mlclient.xquery import cts, fn


def run():
    return cts.element_child_geospatial_values(
        fn.qname("https://example.com/products", "p:item"), "child-names",
    ).compile()
