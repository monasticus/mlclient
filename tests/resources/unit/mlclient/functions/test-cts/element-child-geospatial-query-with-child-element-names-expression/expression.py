from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_query(
        "item",
        fn.qname("https://example.com/products", "p:item"),
        cts.box(10, 10, 20, 20),
    ).compile()
