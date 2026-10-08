from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_element_child_reference(
        fn.qname("https://example.com/products", "p:item"), "child",
    ).compile()
