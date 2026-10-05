from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_element_reference(
        fn.qname("https://example.com/products", "p:item"),
    ).compile()
