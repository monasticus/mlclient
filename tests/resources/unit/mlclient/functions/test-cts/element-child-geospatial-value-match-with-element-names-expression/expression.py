from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_value_match(
        fn.qname("https://example.com/products", "p:item"), "child-names", "prod*",
    ).compile()
